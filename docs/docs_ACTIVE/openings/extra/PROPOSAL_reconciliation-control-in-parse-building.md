# Proposal — a reconciliation control inside `parse_building()`

**Written 2026-08-20 (evening) by the director, at the user's request.**
🔴 **This is a proposal. Nothing here is authorised, and no item ID has been opened.** It touches
production code, which this session does not write, and it would need **both** a user grant and a new
item ID. The next free ID is `OPEN-63`; **opening it is the user's, not mine.**

---

## 1. The pattern, stated plainly

Three defects in four days. **Every one of them was found by an executor auditing its own arithmetic
as a side-effect of some other task. Not one plan asked for the control that found it.**

| Item | Opened | Found by | The defect, in one line |
|---|---|---|---|
| **OPEN-58 (b)** | 2026-08-19 | T04's own controls | A helper read EUI by a formula that **does not match** production's `total_eui_kwh_m2` — up to −24 % absolute |
| **OPEN-60** | 2026-08-19 | a reconciliation control in T01 of the gap-decomposition plan | `total_eui_kwh_m2` **undercounts** Interior Lighting and Interior Equipment when a zone multiplier > 1 — median 4.71 %, **max 192.28 %** |
| **OPEN-61** | 2026-08-20 | a reconciliation control in T01 of the four-board plan | `total_eui_kwh_m2` **drops** the District Heating component of Water Systems — ~1 % where measured, fleet size unknown |

**What they share is not the bug — it is the shape of the bug.** `total_eui_kwh_m2` is assembled by
**summing an enumerated list of named components**, and nothing anywhere compares that sum against
the whole-building total EnergyPlus itself reports. So:

- a term **missing from the list** (OPEN-61: `METER_QUERY` at `parser.py:48-54` has no
  `DistrictHeating` meter of any kind) is silently zero;
- a term **summed at the wrong scale** (OPEN-60: per-zone hourly variables are not multiplier-scaled
  by EnergyPlus, while the floor-area divisor at `parser.py:431-433` **is**) is silently low;
- a **reimplementation of the formula elsewhere** (OPEN-58 b) drifts from it silently.

🔴 **In all three cases the number still looks like a number.** There is no exception, no NaN, no
warning. That is the property worth attacking, and it is the same property that made OPEN-62's parser
return `0.0` areas without complaint.

---

## 2. What already exists, and why it did not catch any of this

`check_building_integrity()` — `openubem/results/parser.py:602-646` — already performs an ABUPS
cross-check and returns `abups_ok`.

**It is imported and called by exactly four scripts**, verified at HEAD:

- `scripts/run_r1_t12.py:186, :211`
- `scripts/run_r3_fleet.py:287, :313`
- `scripts/run_r3_step5.py:178, :204`
- `scripts/run_t12_boston.py:173, :198`

🔴 **`parse_building()` (`parser.py:716`) does not call it.** Every analysis script that goes through
`parse_building()` — which is the normal route — gets no reconciliation at all.

⚠️ **But "just wire it up" is the wrong proposal, and this is the part worth getting right.**
`check_building_integrity()`'s ABUPS query is hard-scoped to two rows and one fuel:

```
RowName IN ('Interior Lighting', 'Interior Equipment')
ColumnName = 'Electricity'
```

That is **exactly OPEN-60's failure mode and nothing else.** It would have caught OPEN-60. It would
**not** have caught OPEN-61 — District Heating under Water Systems is not in its `RowName` list and
not in the `Electricity` column. It would not have caught OPEN-58 (b) either. A proposal that
consists of calling the existing function would close one of three doors and read as though it had
closed all three.

---

## 3. The proposed control

**One scalar reconciliation per building, all fuels, computed where the number is formed.**

Compare the assembled figure against EnergyPlus's own whole-building total:

```
residual = (total_eui_kwh_m2 × resolved_floor_area) − ABUPS_total_site_energy
relative_residual = residual / ABUPS_total_site_energy
```

ABUPS' `Total Site Energy` (or the `End Uses` table's total row) is **a differently-shaped source of
truth**: EnergyPlus computes it independently of the meter enumeration, so **any** term the meter
list omits, mis-scales, or double-counts appears as a non-zero residual. It does not need to know
*which* term is wrong to report that the sum does not close.

**What it would have caught, using each item's own measured size:**

| Item | Residual it would have shown |
|---|---|
| OPEN-61 | **1.03–1.22 %** — above any sane threshold |
| OPEN-60 | median **4.71 %**, p90 24.19 %, max **192.28 %**; only 6 of 48 reconciled within 2 % |
| OPEN-58 (b) | up to **−24 %** absolute |

All three, from one check, in the place all three numbers are made.

---

## 4. Two design cautions, both learned from this repo

🔴 **Caution 1 — a gate that fails loudly gets bypassed, and there is already a precedent here.**
`parse_building()`'s existing `_check_zone_integrity()` assumes the OpenUBEM
`{osm_id}_F{floor}_{label}` zone-naming convention. `layout_assign` buildings keep the DOE baseline's
native names (`"G SW APARTMENT"`), so the gate **false-negatives on every `layout_assign` building**
(defect E-LA-05, still open). The documented response was to bypass `parse_building()` and call
`parse_building_sql()` + `_parse_meters_sql()` + `_compute_eui()` directly
(`scripts/analysis/compare_layout_assign.py:100-102`). **A gate that cries wolf was routed around
rather than fixed, and that is how the parser ended up with no reconciliation at all on the path that
matters.**

**Therefore: record the residual, do not raise on it.** Emit `eui_residual_pct` as an ordinary column
on every parsed row, alongside the existing `abups_ok`. A number in a column cannot be bypassed by
calling a different function, because it travels with the data. Thresholding is a downstream
decision, taken per analysis, on visible values.

⚠️ **Caution 2 — the cost is unsized.** One extra `TabularDataWithStrings` query per building, over
8,160 buildings. Almost certainly negligible against simulation time, but it is **not measured**, and
this register's standing complaint is precisely about changes authorised at unknown size. Size it
before adopting.

---

## 5. What this proposal does *not* claim

- **It does not fix OPEN-60 or OPEN-61.** Both still need a remedy ruling, and both remedy shapes are
  design decisions this brief does not touch. A control that *detects* a missing term is not a
  decision about *where the term should come from*.
- **It does not restate any number.** No adopted figure moves because a column is added.
- **It does not claim the three items would have been caught before doing damage** — only that they
  would have surfaced at the point of parsing rather than by luck, three separate times, in three
  unrelated tasks.
- 🔴 **It does not claim to be complete.** A residual check catches terms that break the *sum*. A
  defect that is self-consistent in both the sum and ABUPS — a wrong floor area, say — passes it
  cleanly. This is one control, not a guarantee.

---

## 6. What is needed from the user

1. **Whether to open an item for it at all** (`OPEN-63` is next free). It is a *preventive control*,
   not a defect, and this register has not previously tracked preventive work as items. Declining is
   a reasonable answer; **"the pattern has been named for three passes and remains unaddressed" is
   the argument for, and it should not be mistaken for urgency about a broken number.**
2. **If opened:** a grant to write production code, since this session does not.

**Recommendation:** open it, and scope the first task to **measure only** — add the residual column,
run it over the existing parsed corpus, and report the distribution. That answers "how often does the
sum fail to close, and by how much" without changing a single published figure, and it sizes the cost
at the same time.

---

## Cites, all verified at HEAD 2026-08-20

- `openubem/results/parser.py:48-54` — `METER_QUERY`, the enumerated meter list (OPEN-61's mechanism).
- `openubem/results/parser.py:431-433` — the multiplier-aware floor-area divisor (OPEN-60's mechanism).
- `openubem/results/parser.py:469` — `dhw_eui_kwh_m2` built from the two Water Systems meters only.
- `openubem/results/parser.py:602-646` — `check_building_integrity()`, the existing gate; its ABUPS
  query is scoped to Interior Lighting + Interior Equipment, Electricity only.
- `openubem/results/parser.py:716` — `parse_building()`, which does not call it.
- `scripts/analysis/compare_layout_assign.py:100-102, :306` — the documented bypass and E-LA-05.
