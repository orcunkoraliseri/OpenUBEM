# PROPOSAL — OPEN-55 remedy: what an `OpenUBEMUnknown` building may be

**Slug:** `PROPOSAL_open-55_unknown-pde-bounds`
**Written:** 2026-08-18 (late), by the director, during the OPEN-48 third fleet run
**Status:** 🟡 **AWAITING THE USER'S RULING.** Nothing is patched. This document proposes; it does not decide.
**⚠️ Read §7A before §7 — a measurement taken after the first draft revised the recommendation from Option B to Option B+.**
**Evidence base:** `extra/INVESTIGATION_open-55_pde-bounds-datacenter.md` (mechanism, dose-response, blast radius)
**Register entry:** `INVESTIGATION_open-items-register.md` § OPEN-55
**Touches:** `openubem/semantic/__init__.py` — one call site (`:366`) and one function (`_build_unknown_loads`, `:225`)

---

## 1. The decision being asked for, in one sentence

When the classifier cannot name a building, the model must still give it a lighting load, an equipment
load, an occupant density and a window-to-wall ratio — and **the question is what population it should
draw those from.** Today the answer is "any of the 29 archetypes, uniformly, including a large
high-ITE data centre." This document argues that is wrong, sets out three ways to fix it, and
recommends one.

**This is a DESIGN question, not a defect fix, which is why it is being put to you rather than
decided.** The code is doing exactly what it was written to do. What is missing is a stated position on
what an unnamed building is allowed to be.

---

## 2. What the code does today

`openubem/semantic/__init__.py:366`:

```python
loads_unk = _build_unknown_loads(out, unk_mask, _get_cross_archetype_loads(), rng)
```

`_get_cross_archetype_loads()` returns the **full 29-row archetype table**. `_build_unknown_loads`
(`:245-256`) then takes the **min and max of each column** over those 29 rows and draws each Unknown
building's value **uniformly between them**:

```python
bounds = {col: (real_loads[col].min(), real_loads[col].max()) for col in pde_cols}
...
result.at[idx, col] = row_rng.uniform(lo, hi)
```

The four columns drawn this way are `lighting_w_m2`, `equipment_w_m2`, `occupant_m2_per_person`, `wwr`.

### 2.1 The 29-row table, sorted by equipment density

| archetype | equip W/m² | archetype | equip W/m² |
|---|---:|---|---:|
| Warehouse | 2.58 | MediumOfficeDetailed | 10.76 |
| SmallHotel | 2.91 | Hospital | 10.76 |
| SmallOffice | 6.78 | Outpatient | 10.76 |
| SmallOfficeDetailed | 6.78 | LargeOffice | 10.76 |
| Courthouse | 6.90 | LargeOfficeDetailed | 10.76 |
| MidriseApartment | 7.53 | TallBuilding | 10.76 |
| HighriseApartment | 7.53 | SuperTallBuilding | 10.76 |
| LargeHotel | 7.53 | SuperMarket | 10.98 |
| RetailStripmall | 7.64 | PrimarySchool | 16.15 |
| College | 10.00 | SecondarySchool | 16.15 |
| MediumOffice | 10.76 | Laboratory | 43.06 |
| RetailStandalone | 10.76 | FullServiceRestaurant | 59.20 |
| | | QuickServiceRestaurant | **96.88** |
| | | *— gap, 4.4× —* | |
| | | SmallDataCenterLowITE | 430.56 |
| | | SmallDataCenterHighITE | 1076.39 |
| | | LargeDataCenterLowITE | 1076.39 |
| | | **LargeDataCenterHighITE** | **5381.96** |

**Twenty-five of twenty-nine archetypes sit at or below 16.15 W/m².** The four data centres are not a
tail of the same distribution; they are a different kind of building that happens to live in the same
table.

---

## 3. 🔴 The part that is usually missed: with a uniform draw, the maximum sets the *centre*

The instinct is that admitting `LargeDataCenterHighITE` widens a tail. It does not. The draw is
**uniform**, so the bound does not add an unlikely extreme — **it relocates the typical value.**

| donor pool | equipment bounds | **median draw** |
|---|---|---:|
| all 29 archetypes *(today)* | `[2.58, 5381.96]` | **2692.27 W/m²** |
| 25 non-data-centre archetypes | `[2.58, 96.88]` | **49.73 W/m²** |
| *for reference:* `MediumOffice`, the envelope donor | — | 10.76 W/m² |

**Half of all Unknown buildings today receive more than 2,692 W/m² of equipment load** — roughly 250×
an ordinary commercial building. This is not an edge case that occasionally fires. It is the middle of
the distribution, and it is why the failures scale with the Unknown count rather than appearing
sporadically.

The same defect exists, more quietly, on the occupancy axis:

| donor pool | `occupant_m2_per_person` | median draw |
|---|---|---:|
| all 29 *(today)* | `[4.65, 464.52]` | **234.6 m²/person** |
| excluding data centres and `Warehouse` | `[4.65, 92.90]` | 48.8 m²/person |

A median Unknown building is currently assigned **one occupant per 235 m²** — effectively unoccupied.
That does not crash EnergyPlus, so it has never been caught by a gate, and it is silently present in
every fleet figure produced from post-fix code.

**Lighting `[3.44, 19.38]` and WWR `[0.10, 0.40]` are both fine.** The defect is confined to the two
columns where the table contains a categorically different building type.

---

## 4. What OPEN-49 did and did not do

The line before the OPEN-49 fix (commit `fe05509`), and after it (commit `82bbd25`):

```python
- loads_unk = _build_unknown_loads(out, unk_mask, loads_real if real_mask.any() else _get_cross_archetype_loads(), rng)
+ loads_unk = _build_unknown_loads(out, unk_mask, _get_cross_archetype_loads(), rng)
```

🔴 **The full-table fallback was already there.** It fired only when a cell contained *no* classified
buildings at all. So the data-centre bound is not a defect OPEN-49 introduced — it is a defect OPEN-49
**made universal**, by removing the condition that had been hiding it.

Two things follow, and both matter for the ruling:

1. **OPEN-49's fix was correct and must not be reverted.** Making the bounds depend on which
   archetypes happen to occur in a cell is precisely the cell-composition dependence OPEN-49 existed
   to remove. Reverting trades a visible defect for the invisible one that cost this arc two fleet runs.
2. **The pre-OPEN-49 code was never sound either.** Any all-Unknown cell would have hit the same
   bounds. "It worked before" is true only in the sense that the path was rarely taken.

---

## 5. The strongest argument for changing it: the row already contradicts itself

`_build_unknown_envelope` (`:189-210`) assigns every Unknown building the donor archetype
`MediumOffice` at `DOERefPre1980` vintage — `_DONOR_ARCH = "MediumOffice"` at `:82`. So the **envelope**
half of an Unknown row states a clear position: *an Unknown building is an ordinary medium office we
failed to name.*

The **loads** half of the same row states a different position: *an Unknown building is any of 29
archetypes with equal probability, including a data centre.*

**These are two incompatible answers to the same question, in the same function, applied to the same
building.** Whatever is decided below, the two halves should agree — and the envelope half is the one
that already has a defensible rationale written next to it.

---

## 6. Options

### Option A — revert `:366` to the pre-OPEN-49 conditional

Bounds come from the archetypes present in the cell when any exist.

- ✅ Restores plausible loads in mixed cells with no new concepts.
- ❌ **Reintroduces the exact cell-composition dependence OPEN-49 removed**, and OPEN-49 cannot then close.
- ❌ Leaves all-Unknown cells drawing data-centre loads.
- **Rejected.** It trades a defect that crashes for a defect that silently biases.

### Option B — screen the donor pool by building kind *(recommended)*

Keep the fixed, cell-independent table, but exclude from the **Unknown donor pool** the archetypes that
are not candidate interpretations of an unnamed building: the four data centres on every column, and
`Warehouse` on the occupancy column only.

- ✅ Keeps everything OPEN-49 bought — the pool is a fixed property of the archetype table, identical in
  every cell, so the draw stays cell-independent and reproducible.
- ✅ Smallest possible change: a constant and one filter. No new distribution, no new parameter, nothing
  fitted.
- ✅ Directly falsifiable — see §8.
- ⚠️ Requires stating the screen explicitly, because it is a judgement about which archetypes an
  unnamed building may be. That statement is what this document asks you to approve.

### Option C — anchor the draw on the envelope donor

Draw around `MediumOffice` with a bounded spread instead of uniformly across a pool.

- ✅ Most coherent — it makes §5's contradiction go away by construction.
- ❌ **Invents a distribution shape the DESIGN never specified** (which spread? which family?). That is a
  modelling decision requiring a spec, not a defect remedy, and it would need its own validation.
- **Recorded as the better long-run answer, not proposed for now.**

### Option D — clip the bounds to percentiles instead of min/max

Measured, and it does not work: the 5th–95th percentiles of the equipment column are
**`[4.46, 1076.39]`** — the 95th percentile is *still a data centre*, because 4 of 29 rows (13.8 %) are
data centres. **Rejected on measurement, not on taste.**

---

## 7. The recommendation

**Option B.** Concretely:

```python
# openubem/semantic/__init__.py
_UNKNOWN_DONOR_EXCLUDE = {
    "SmallDataCenterLowITE", "SmallDataCenterHighITE",
    "LargeDataCenterLowITE", "LargeDataCenterHighITE",
}
_UNKNOWN_DONOR_EXCLUDE_OCCUPANCY = _UNKNOWN_DONOR_EXCLUDE | {"Warehouse"}
```

applied inside `_build_unknown_loads` when the per-column bounds are computed, so the exclusion is
visible at the point where the bound is taken rather than hidden at the call site.

Resulting bounds: equipment `[2.58, 96.88]`, occupancy `[4.65, 92.90]`, lighting and WWR unchanged.

**Why this and not the others:** it is the only option that fixes the physics without either undoing
OPEN-49 (A) or introducing an unspecified modelling assumption (C), and D was measured to fail. It also
adds **zero fitted parameters**, which the adopted baseline's headline claim depends on.

---

---

## 7A. 🟢 Option B has already been observed — and it is not sufficient

Written 2026-08-18 21:0x, after the T05 per-cell comparison
(`scripts/analysis/open48_run3_vs_run2_cell_delta.py`). This section changes the strength of the
recommendation above and should be read with it.

**Run 2's `nyc_rural` is an accidental experiment on exactly the bounds Option B proposes.** Run 2
predates the OPEN-49 fix, so its Unknown bounds came from the archetypes present in that cell. The
cell's archetypes are `SmallOffice` ×150, `MidriseApartment` ×22, `FullServiceRestaurant` ×6,
`Courthouse` ×4, `SmallHotel` ×4, `QuickServiceRestaurant` ×3, and four singletons — **no data centre.**
Its equipment ceiling was therefore `QuickServiceRestaurant` at **96.88 W/m²**, which is *precisely the
ceiling Option B produces.*

| `nyc_rural` Unknown | run 2 — bounds `[2.58, 96.88]` *(= Option B)* | run 3 — bounds `[2.58, 5381.96]` *(today)* |
|---|---|---|
| `way/334332606` | success, equip 387.4, total 583.4 | **failed, dropped** |
| `way/772627007` | success, equip 304.8, total 545.9 | success, equip **13 824.4**, total **17 140.2** |
| `way/801981473` | success, equip 314.4, total 508.9 | **failed, dropped** |
| `way/1103897842` | success, equip 61.2, total 287.8 | **failed, dropped** |
| `way/1103897844` | success, equip 185.2, total 520.9 | success, equip **11 862.5**, total **14 744.0** |

*(EUI in kWh/m²·yr. Cell mean over classified buildings: **233.4**.)*

**What this establishes, as observation rather than prediction:**

✅ **Option B stops the crashes.** All five Unknowns simulated successfully under `[2.58, 96.88]`. The
§8 acceptance test is therefore very likely to pass — this is no longer a hoped-for outcome.

🔴 **Option B does not deliver physical plausibility.** Under those same bounds an Unknown building
still lands at **387 kWh/m² of equipment EUI against a cell mean of 233 kWh/m² total** — the unnamed
building consumes more on equipment alone than a typical building in the cell consumes altogether.
That is a quick-service restaurant's kitchen applied to a building we could not name. It does not crash,
so no gate catches it, and it flows straight into the fleet figure.

**This materially strengthens the second ruling offered in §9.** Excluding `Laboratory` (43.06),
`FullServiceRestaurant` (59.20) and `QuickServiceRestaurant` (96.88) as well drops the ceiling to
**16.15 W/m²** (`PrimarySchool` / `SecondarySchool`) and the uniform median from 49.73 to **9.37 W/m²** —
against `MediumOffice`'s 10.76, the archetype the envelope half of the same row already assigns. **The
two halves of an Unknown row would then agree**, which is the §5 argument, satisfied without inventing
a distribution.

### Revised recommendation

**Option B is the floor, not the answer.** I now recommend the wider screen — call it **B+**:

| | excluded from the Unknown donor pool | equip bounds | median draw |
|---|---|---|---|
| B | 4 data centres | `[2.58, 96.88]` | 49.73 |
| **B+** *(now recommended)* | 4 data centres · `Laboratory` · both restaurants | **`[2.58, 16.15]`** | **9.37** |
| both | `Warehouse` additionally, on the occupancy column only | occ `[4.65, 92.90]` | 48.8 |

**Why the change is honest rather than opportunistic:** B was recommended before this measurement
existed, on the argument that the table has a categorical break at the data centres. That argument is
still true, and B is still strictly better than today. What the measurement adds is that **the break at
the data centres is where the *crashes* stop, not where the *implausibility* stops** — and the original
recommendation could not distinguish those two thresholds because no cell had yet been observed running
at exactly the B bound. One now has.

**What B+ costs that B does not:** a defensible line has to be drawn at a smaller gap. 16.15 → 43.06 is
a 2.7× step, against 96.88 → 430.56 at 4.4×. It is a weaker natural break, and the exclusion of
restaurants and laboratories is more clearly a judgement about what an unnamed building may be. **That
judgement is exactly what §1 says is yours to make**, and it is why this is still a proposal.

## 8. 🔴 How to know whether it worked — falsifiable, and cheap

The remedy makes a **hard prediction** on data that already exists:

> `nyc_suburban` — 1,589 buildings, 290 Unknown, **71 divergences today** — must return
> **zero divergences** after the screen, with **no other change**, on its frozen `01_buildings.gpkg`.

The prediction is sharp because the failure threshold is measured: **nothing below ~2,496 W/m² failed**,
and the screened ceiling is **96.88 W/m²** — a factor of 26 below the lowest observed failure. If any
building still diverges, the mechanism in the OPEN-55 investigation is incomplete and this remedy is
not the whole story.

Cost: one cell, ~45 min, inputs already seeded on disk. **No fleet run is needed to test this.**

Secondary check, which must be done in the same pass: the fleet EUI will move, because ~half of all
Unknown buildings currently carry an absurd equipment load and the occupancy median moves from
235 → 49 m²/person. **That movement is a correction, not a regression**, and it must be reported as a
number rather than absorbed silently.

---

## 9. What this does **not** claim

- **It does not touch the published `157.1`.** The adopted `phaseE_elevrb` run and run 2 both predate
  the OPEN-49 fix, so neither drew from the widened bounds. OPEN-55 is a defect in the repository's
  *current* code, not in the adopted result.
- **It does not close OPEN-49.** OPEN-49 stays open until this is settled, because its fix is what made
  the defect universal.
- **It does not rescue run 3.** Eight of twelve cells stopped; no aggregate figure is recoverable from
  that run under any remedy applied afterwards.
- **It does not claim the screen is the only defensible one.** `Laboratory` (43.06) and the two
  restaurants (59.20, 96.88) are also arguably not candidate readings of an unnamed building. Excluding
  them would drop the ceiling to 16.15 W/m². **That is a second, narrower ruling available to you**, and
  the recommendation deliberately does not take it — it stops at the one place where the table has a
  4.4× gap and a categorical difference in building kind.

---

## 10. What is being asked

1. **Approve Option B**, or rule otherwise.
2. **Confirm the width of the screen.** Four data centres only (**Option B**), or data centres plus
   `Laboratory` and both restaurants (**Option B+**, equipment ceiling 16.15 W/m² — **now recommended,
   see §7A**). This is the substantive half of the ruling; option A was rejected on reasoning and D on
   measurement, so the real question is only where the line falls.
3. On approval, the patch is one constant plus one filter, executed by a fresh Sonnet against a plan
   doc, with the `nyc_suburban` test of §8 as the acceptance criterion.

**Nothing will be patched before that ruling.**
