# MEASUREMENT — OPEN-48 third fleet run, and the CP-2 / CP-3 rulings

**Slug:** `MEASUREMENT_open-48_third-fleet-run`
**Date:** 2026-08-18 (late)
**Plan:** `implemenation/previous/PLAN_open-48-third-fleet-run-2026-08-18.md` (T05, CP-2, CP-3)
**Run:** `open48_refleet3`, launched 17:44:49, T02 complete 20:47
**Rulings:** delegated to the director by the user on 2026-08-18 —
*"tu progress comme tu recommends en choissant l'option de plus precision"*. The delegation covers the
choice; the reasoning is shown here in full.

---

## 1. The one-paragraph answer

**The run did not produce a fleet figure, and it should not be made to.** Five of twelve cells stopped
on a defect the run itself uncovered (OPEN-55), and four of the five that passed did so by deleting the
buildings that defect had touched. **But the run was not wasted, and it answered its actual question
better than an aggregate would have.** Measured per cell, on frozen input, with code as the only
variable: **the OPEN-49 fix is worth approximately zero on classified buildings — ≤ 0.09 kWh/m², under
0.08 % — and every kilowatt-hour of visible movement comes from a handful of Unknown buildings.** The
published **157.1 stays** (CP-3), with one caveat now quantified for the first time.

---

## 2. CP-1 — where the twelve cells landed

| outcome | n | cells (failures / tolerance) |
|---|---:|---|
| **stopped** | **5** | `nyc_suburban` 71/16 · `nyc_urban` 83/18 · `la_centre` 10/5 · `austin_centre` 20/5 · `austin_suburban` 14/5 |
| passed | 5 | `nyc_rural` 3/5 · `la_rural` 5/5 · `la_suburban` 0/13 · `austin_rural` 4/5 · `austin_urban` 5/5 |
| transport only, no verdict | 2 | `nyc_centre` (`:265`) · `la_urban` (`:327`) |

Two of the five stops (`austin_centre`, `austin_suburban`) exited `rc=1` and had to be recovered from
their logs — see OPEN-54 §3.4. **Classify by `ZERO-FAIL` in the log, never by return code.**

⚠️ An earlier draft of this table said eight stopping cells. That was my arithmetic error, corrected
here and in OPEN-55 §4A.6.

---

## 3. T05 — the measurement that survives

`scripts/analysis/open48_run3_vs_run2_cell_delta.py` →
`openubem/outputs/comparisons/open48_run3_vs_run2_cell_delta.csv`

Run 3 against run 2, per cell. The OSM input is byte-identical (run 3's work dirs were pre-seeded with
run 2's cached `01_buildings.gpkg`), so **code is the only variable.** Three guards, each of which
changed the answer when added:

1. only `simulation_status == "success"` rows count — failed rows carry `NaN` EUI but a real floor
   area, and including them deflates the weighted mean;
2. only buildings successful in **both** runs count, so no delta reflects a difference in which
   buildings were dropped;
3. `delta_known` repeats the comparison with **every Unknown removed from both runs**, so the OPEN-55
   contamination is excluded by construction rather than assumed small.

| cell | n common | Unknown in common | Δ all common | **Δ known only** |
|---|---:|---:|---:|---:|
| `nyc_rural` | 195 | 2 | **+23.2685** | **+0.0004** |
| `austin_rural` | 241 | 3 | **+12.9387** | **−0.0001** |
| `la_suburban` | 1343 | 2 | **+1.9560** | **+0.0001** |
| `la_rural` | 144 | 0 | −0.0906 | −0.0906 |
| `austin_urban` | 420 | 0 | −0.0614 | −0.0614 |

*(kWh/m²·yr, floor-area weighted, `open43` arithmetic.)*

### 3.1 🟢 Finding 1 — the OPEN-49 fix is worth nothing on classified buildings

**Every classified building in every comparable cell changed value, and the cell means did not move.**
`nyc_rural`: 195 of 195 buildings changed, cell mean moved **+0.0004**. `la_suburban`: 1343 of 1343
changed, **+0.0001**. `austin_rural`: 241 of 241 changed, **−0.0001**.

That is exactly the signature of route 1 of the fix — reseeding the draw per building
(`blake2b(osm_id)`) instead of per cell-sized block. It **redistributes** draws between buildings
without changing the population they come from, so individual buildings move and the aggregate does
not. The two cells with no Unknowns at all bound the residual: **`la_rural` −0.0906 and `austin_urban`
−0.0614, i.e. −0.075 % and −0.035 %.**

🔴 **This retires the premise the arc has been running on.** Three fleet runs were spent asking what the
OPEN-49 window-randomisation fix was worth in fleet kWh/m². **Measured: nothing outside noise.** The
question is answered, and answered in the negative.

### 3.2 🔴 Finding 2 — the entire visible delta is a handful of Unknown buildings

The gap between the two Δ columns is the whole story. In `nyc_rural`, **two buildings out of 195 move
the cell mean by +23.27 kWh/m², about +10 %.** In `austin_rural`, **three of 241 move it +12.94.**

The mechanism, read directly off the two runs' own result rows for `nyc_rural`:

| Unknown building | run 2 — bounds `[2.58, 96.88]` | run 3 — bounds `[2.58, 5381.96]` |
|---|---|---|
| `way/334332606` | success, equip 387.4, total 583.4 | failed, dropped |
| `way/772627007` | success, equip 304.8, total 545.9 | success, equip **13 824.4**, total **17 140.2** |
| `way/801981473` | success, equip 314.4, total 508.9 | failed, dropped |
| `way/1103897842` | success, equip 61.2, total 287.8 | failed, dropped |
| `way/1103897844` | success, equip 185.2, total 520.9 | success, equip **11 862.5**, total **14 744.0** |

*(kWh/m²·yr. Cell mean over classified buildings: 233.4.)* Two survivors at roughly **73× the cell
mean**, in a cell that passed its gate and would have been aggregated without comment.

### 3.3 ✅ The non-vacuity control

The plan's control was the elevator column, not the delta. `nyc_rural`: **27 buildings with non-zero
`elevators_eui_kwh_m2`, Σ 97.1, identical in run 2 and run 3.** Elevator energy is present and was not
disturbed by either fix. The comparison is not measuring an empty pipeline.

---

## 4. 🔴 CP-2 RULING — do not aggregate run 3

**Ruled: run 3 produces no fleet figure. No aggregate is to be computed, published, or quoted from it,
including from the five passing cells.**

Three independent reasons, any one sufficient:

1. **Five cells produced no results at all.** A twelve-cell fleet figure from seven cells is not the
   quantity `157.0552` is comparable to.
2. **The five passes are not poolable, and the distortion runs in both directions.** Four passed *by
   dropping* the affected buildings — and the drop is selective, removing exactly the highest draws.
   `austin_urban` dropped **5 of its 5** Unknowns and was recorded as clean. `la_suburban` **kept** both
   of its Unknowns and was also recorded as clean. Two cells, same run, same label, opposite biases.
   Neither is quantifiable from the artifacts, and pooling does not cancel them.
3. **It would answer a question nobody asked.** §3.1 already answers the question the run was launched
   for, per cell, more precisely than any pooled number could — because pooling would have buried a
   0.0004 signal under a 23.27 contaminant.

**Under the user's criterion — take the more precise option — the precise output of this run is the
per-cell table in §3, not a fleet scalar.** A scalar here would be less precise *and* less true.

---

## 5. 🔴 CP-3 RULING — the published 157.1 stays, with one caveat now quantified

**Ruled: `157.0552` (published as 157.1) remains the adopted fleet figure. It is not moved, not
withdrawn, and not annotated as suspect.**

### Why it stays

1. **Nothing measured displaces it.** Run 3 produced no competing figure, and run 2's `159.2157` was
   never a candidate — its `+2.1605` was a fresh OSM fetch drifting the classification, not a modelling
   result.
2. **The defect found in this run cannot touch it.** OPEN-55 lives in code committed *after* the adopted
   run and after run 2. Neither drew from the widened bounds.
3. **The reason the arc doubted it has now been measured and dismissed.** OPEN-48 stayed open on the
   absence of a post-fix re-run. That re-run now exists, and §3.1 shows the fix it was testing moves
   classified buildings by **under 0.08 %**. There is no longer a mechanism on the table by which the
   adopted figure is wrong for the reason this arc suspected.

### ⚠️ The caveat, which must be stated wherever the figure is published

**The adopted run contains the pre-fix version of the same Unknown-path defect, and its size is now
measurable — on run 2, which shares that code path.**

| run 2, all twelve cells | value |
|---|---|
| pooled EUI, all 8,154 successful buildings | **159.2157** |
| pooled EUI, 7,504 **classified** buildings only | **155.1577** |
| **contribution of the Unknown path** | **+4.058 kWh/m² (+2.615 %)** |
| Unknown buildings | 650 — **3.7 % of floor area, mean EUI 264.9** vs fleet 159.2 |

Per cell it ranges from **0.000** (`la_rural`, no Unknowns) to **+18.65** (`nyc_suburban`, 290 Unknowns).

🔴 **The Unknown-path inflation in run 2 (+4.06) is nearly twice the entire adopted-vs-run-2
discrepancy (+2.16) that this arc has spent three fleet runs chasing.** The arc was measuring the
smaller of two effects while the larger sat inside both runs uncosted.

**What is *not* claimed:** the adopted run's own per-building results no longer exist, so its Unknown
inflation cannot be measured, only inferred from run 2's shared code path and comparable Unknown share.
**+4.06 is a measurement on run 2 and an estimate for the adopted run — it is not a correction to
apply.** Subtracting it would be inventing a figure. The honest statement is: *157.1 stands as the
adopted result, and carries an Unknown-path bias of order 2–3 % that has never been separately
reported.*

### What would settle it

The OPEN-55 ruling (`extra/PROPOSAL_open-55_unknown-pde-bounds.md`, awaiting the user) fixes the
Unknown path. A fleet run **after** that ruling, on the frozen inputs still on disk, would produce the
first figure free of this bias in either direction. **That, not run 3, is the run that could move
157.1.**

---

## 6. What each open item takes from this

| item | effect |
|---|---|
| **OPEN-48** | 🟢 **Closeable.** Its stated blocker — no post-fix fleet re-run exists — is discharged. The re-run exists, and its result is §3.1: the fix is worth ≈0 on classified buildings. |
| **OPEN-49** | 🔴 **Stays open.** Its own fix made OPEN-55 universal; it cannot close before the OPEN-55 ruling. |
| **OPEN-54** | 🔴 Widened twice. Four call sites fired in one run, and it was shown to bias classification, not merely cost reruns (§3.4 of that doc). |
| **OPEN-55** | 🔴 Open, remedy proposed, **awaiting the user's ruling on the width of the screen (B vs B+).** |

---

## 7. Artifacts

| path | what |
|---|---|
| `scripts/analysis/open48_run3_vs_run2_cell_delta.py` | the T05 comparison, with its three guards |
| `openubem/outputs/comparisons/open48_run3_vs_run2_cell_delta.csv` | its output, twelve rows |
| `extra/INVESTIGATION_open-55_pde-bounds-datacenter.md` | mechanism, dose-response, per-cell scoreboard |
| `extra/INVESTIGATION_open-54_ssh-unchecked-exit.md` | the transport defect and the misclassification argument |
| `extra/PROPOSAL_open-55_unknown-pde-bounds.md` | the remedy, awaiting ruling |
| `%TEMP%/open48_run3/*.log` | twelve cell logs + `nyc_centre_t03.log` |
