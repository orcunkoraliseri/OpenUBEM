# INVESTIGATION — the OPEN-49 fix widened the PDE bounds to the full archetype table, and Unknown buildings now draw data-centre equipment loads

**Slug:** `open-55_pde-bounds-datacenter`
**Opened:** 2026-08-18, during the OPEN-48 third fleet run
**Trigger:** `nyc_suburban` died `rc=2` at 18:46 — 71 EnergyPlus divergences against a tolerance of 16
**Status:** diagnosed, mechanism proven, blast radius measured; **remedy specified, not applied** (§7)
**Related:** OPEN-49 (the fix that caused this), OPEN-48 (the run that exposed it),
`implemenation/previous/PLAN_open-48-third-fleet-run-2026-08-18.md` T02

---

## 1. The finding in one paragraph

The OPEN-49 fix has a side effect that was not part of its intent. In making the cross-archetype load
table **unconditional**, it widened the bounds of the Unknown-building parameter draw from *the
archetypes present in the cell* to *all 29 archetypes in the table* — which include
`LargeDataCenterHighITE` at **5381.96 W/m² equipment power density**. Unknown buildings are now assigned
equipment densities drawn uniformly on `[2.58, 5381.96]` W/m². In `nyc_suburban` this made
**71 of 290 Unknown buildings diverge** in EnergyPlus, with reported surface temperatures up to
1.3 × 10⁷ °C. The same cell, on **byte-identical input**, returned `{'success': 1589}` in run 2.

**This is a physical-plausibility regression introduced by a correctness fix.** It is not a transient,
it is not infrastructure, and it does not go away on retry.

---

## 2. What was observed

`nyc_suburban` cleared every local stage cleanly:

- Step 1 loaded the seeded cache — **1589 buildings, no OSM fetch**, exactly as run 3 intends
- Step 2 classified 1589, **290 `OpenUBEMUnknown` (18.3 %)** — identical to run 2's 290
- Step 3 generated **1589/1589 IDFs**; both LIVE_SMOKE gates PASS
- Simulation returned **1518 success / 71 failed**, and the drop-tolerance gate stopped the cell:

```
[nyc_suburban] ZERO-FAIL: 71 failures exceed tolerance 16. STOP.
```

Every one of the 71 errors is the same class:

```
** Severe ** CalcHeatBalanceInsideSurf: The temperature of 12669512.96 C
    for zone="WAY/813473624_F0_WHOLE", for surface="BLOCK ... STOREY 0 WALL 0001"
```

A heat balance that runs away to 10⁵–10⁷ °C is the signature of an internal gain the envelope cannot
possibly reject — not a geometry fault, not a schedule fault.

---

## 3. The mechanism, proven

`_build_unknown_loads` (`openubem/semantic/__init__.py:225`) draws four parameters for each Unknown
building by uniform PDE over the min/max of a donor table:

```python
bounds = {col: (real_loads[col].min(), real_loads[col].max()) for col in pde_cols}
...
row_rng = _per_building_rng(osm_id)
for col in pde_cols:
    lo, hi = bounds[col]
    result.at[idx, col] = row_rng.uniform(lo, hi)
```

The OPEN-49 fix changed **what `real_loads` is**. The call site (`:366`) now reads:

```python
loads_unk = _build_unknown_loads(out, unk_mask, _get_cross_archetype_loads(), rng)
```

`_get_cross_archetype_loads()` is now called **unconditionally** — that was route 2 of the fix, and its
stated purpose was sound: *"bounds/medians no longer depend on which archetypes happen to be present in
the cell."* Cell-dependent bounds were a genuine defect, because they made one building's parameters a
function of its neighbours.

**But the replacement bound is not physically screened.** The full table's equipment column is topped by
four data-centre archetypes:

| archetype | equipment_w_m2 |
|---|---|
| `LargeDataCenterHighITE` | **5381.96** |
| `SmallDataCenterHighITE` | 1076.39 |
| `LargeDataCenterLowITE` | 1076.39 |
| `SmallDataCenterLowITE` | 430.56 |
| `QuickServiceRestaurant` | 96.88 |
| `FullServiceRestaurant` | 59.20 |

`nyc_suburban` contains five archetypes — `MidriseApartment`, `SmallOffice`, `MediumOffice`,
`Courthouse`, `QuickServiceRestaurant`. So:

- **pre-fix bound (cell-local):** equipment ∈ `[…, 96.88]`
- **post-fix bound (full table):** equipment ∈ `[2.58, 5381.96]`

**a 55× widening of the upper bound.** The median draw moves from roughly 50 W/m² to roughly 2690 W/m².
For reference, ordinary residential and small-office equipment density is **5–20 W/m²**.

### 3.1 The draw predicts the failure

The draw is deterministic — `_per_building_rng` is `blake2b(osm_id)` mixed with `config.RANDOM_SEED`, by
design, so that runs reproduce. Regenerating all 290 Unknown draws and joining them to the simulation
manifest:

| outcome | count | min equip | median equip | max equip |
|---|---|---|---|---|
| converged | 219 | 6.6 | 2001.1 | 4944.4 |
| **diverged** | **71** | **2496.4** | **4409.6** | **5349.0** |

**No building drawing below 2496 W/m² failed.** Divergence is confined entirely to the top of the drawn
range, and every failure is an `OpenUBEMUnknown` — not one of the 1299 classified buildings failed.

The overlap between 2496 and 4944 (converged buildings drawing into the failing range) is expected:
whether a given gain diverges also depends on envelope area, zone volume and HVAC capacity. The
threshold is soft. **The association is not.**

---

## 4. Blast radius — measured across all twelve cells

Because the draw is deterministic and the inputs are frozen, every cell's draws were regenerated
locally, without simulating anything. Using **2496.4 W/m²** (the lowest observed divergent draw) as a
screening floor:

| cell | buildings | Unknown | Unknown % | draws ≥ floor | tolerance | gate |
|---|---|---|---|---|---|---|
| nyc_suburban | 1589 | 290 | 18.3 | 155 | 15 | **STOP (observed: 71 fails)** |
| nyc_urban | 1779 | 228 | 12.8 | 117 | 17 | **STOP** |
| austin_centre | 413 | 37 | 9.0 | 23 | 5 | **STOP** |
| nyc_centre | 738 | 35 | 4.7 | 17 | 7 | **STOP** |
| austin_suburban | 437 | 24 | 5.5 | 13 | 5 | **STOP** |
| la_centre | 226 | 15 | 6.6 | 7 | 5 | **STOP** |
| austin_rural | 245 | 7 | 2.9 | 5 | 5 | passes |
| nyc_rural | 198 | 5 | 2.5 | 4 | 5 | passes (**observed `rc=0`**) |
| austin_urban | 425 | 5 | 1.2 | 2 | 5 | passes |
| la_urban | 618 | 2 | 0.3 | 2 | 6 | passes |
| la_suburban | 1343 | 2 | 0.1 | 0 | 13 | passes |
| la_rural | 149 | 0 | 0.0 | 0 | 5 | passes |

⚠️ **The screening floor overestimates failures** — `nyc_suburban` had 155 draws above it but only 71
actual divergences, a rate of about 46 %. Applying that rate, the expected stops are `nyc_suburban`,
`nyc_urban`, `austin_centre` and marginally `nyc_centre` / `austin_suburban`. **Between four and six
cells of twelve.** The exact figure is being measured, not estimated — the run is being allowed to
finish for that reason (§6).

### 4.1 The part that matters more than the failures

**A cell passing the gate is not a clean cell.** `la_urban` passes with two Unknown buildings — and
*both* drew above 2496 W/m². They will converge, produce a finite EUI, and that EUI will be enormous.
The gate only catches buildings whose heat balance *diverges*; it is blind to buildings that merely
absorb an absurd load and report it.

So the contamination is **not** proportional to the failure count. Every Unknown building in every cell
is drawing from a distribution whose median is ~2690 W/m². The failures are the visible tail of a
distortion that affects the whole Unknown population — and Unknown is **18.3 %** of `nyc_suburban` and
**12.8 %** of `nyc_urban`, the two largest cells in the fleet.

**Any fleet EUI computed from run 3 is inflated by this, including from the cells that pass.**

---

## 4A. 🟢 Second observation — `nyc_urban`, and the dose-response curve

**Added 2026-08-18 19:42.** `nyc_urban` stopped `rc=2`: **83 of 228 Unknown buildings failed**, against a
tolerance of 18. §4's projection for this cell was "STOP", and it stopped. Two observed cells now exist,
so the screening floor of §4 can be replaced with something far better than a threshold.

**Pooling both cells (518 Unknown buildings, 154 failures) and binning by the drawn equipment density:**

| drawn equipment_w_m² | n | failed | failure rate |
|---|---|---|---|
| 0 – 500 | 39 | 0 | **0.000** |
| 500 – 1000 | 46 | 0 | **0.000** |
| 1000 – 1500 | 53 | 0 | **0.000** |
| 1500 – 2000 | 56 | 1 | 0.018 |
| 2000 – 2500 | 54 | 2 | 0.037 |
| 2500 – 3000 | 53 | 4 | 0.075 |
| 3000 – 3500 | 49 | 15 | 0.306 |
| 3500 – 4000 | 47 | 24 | 0.511 |
| 4000 – 4500 | 47 | 40 | 0.851 |
| 4500 – 5000 | 43 | 37 | 0.860 |
| 5000 – 5400 | 31 | 31 | **1.000** |

**The curve is monotonic across eleven bins, runs from exactly 0.000 to exactly 1.000, and is flat at
zero for every draw below 1500 W/m².** That is a dose-response relationship, not an association. Together
with the fact that **not one of the 3,078 classified buildings in the two cells failed** — all 154
failures are `OpenUBEMUnknown`, in both cells independently — the causal claim in §3 is as well
supported as this kind of evidence gets without a controlled re-run.

It also sharpens the mechanism: divergence is not a cliff at some magic number. It is a **probability
that rises with the injected gain**, which is exactly what one expects when whether the heat balance
runs away also depends on envelope area, zone volume and installed HVAC capacity.

### 4A.1 Revised fleet projection — and predictions recorded *before* the observations

Applying the empirical per-bin rate to every cell's regenerated draws:

| cell | buildings | Unknown | expected failures | tolerance | verdict |
|---|---|---|---|---|---|
| nyc_urban | 1779 | 228 | **83** | 17 | ✅ **OBSERVED STOP** |
| nyc_suburban | 1589 | 290 | **71** | 15 | ✅ **OBSERVED STOP** |
| austin_centre | 413 | 37 | 14.4 | 5 | 🔴 predicted STOP |
| nyc_centre | 738 | 35 | 10.7 | 7 | 🔴 predicted STOP |
| austin_suburban | 437 | 24 | 8.9 | 5 | 🔴 predicted STOP |
| la_centre | 226 | 15 | 3.9 | 5 | predicted pass (**marginal**) |
| austin_rural | 245 | 7 | 2.8 | 5 | predicted pass |
| nyc_rural | 198 | 5 | 1.6 | 5 | ✅ **observed pass** (`rc=0`) |
| la_urban | 618 | 2 | 1.1 | 6 | predicted pass |
| austin_urban | 425 | 5 | 0.7 | 5 | predicted pass |
| la_suburban | 1343 | 2 | 0.0 | 13 | predicted pass |
| la_rural | 149 | 0 | 0.0 | 5 | predicted pass |

**Five of twelve cells stop.** §4's estimate of "four to six" was right, and is now narrowed.

🔴 **These are written down before the cells finish, deliberately.** The remaining seven cells are an
out-of-sample test of the mechanism, and the record should show the prediction preceding the result.
Two are especially sharp:

- **`nyc_centre` is predicted to fail `rc=2` on its T03 retry** — 10.7 expected against a tolerance of 7.
  It has so far failed only `rc=1`, on transport (OPEN-54), so its model outcome is genuinely unseen.
  **If it retries clean, this model is wrong and §4A must be revisited.**
- **`la_centre` is the marginal call** at 3.9 against 5. Either outcome is consistent; it is reported
  because a model that only predicts easy cases is not being tested.

**Nothing about the ruling depends on which way these land.** Five confirmed stops already make a
twelve-cell fleet impossible, and §4.1's contamination argument never depended on the failure count at
all.

---

### 4A.2 ⚠️ Correction — the model predicts *mechanism-attributable* failures, not total failures

**Added 2026-08-18 20:06, after `la_rural` returned `rc=0` with 5 failures against a predicted 0.**

§4A.1 recorded "0.0 expected failures" for `la_rural`, which has **no Unknown buildings at all**.
`la_rural` then finished `rc=0` — but with **five failed buildings**. Taken at face value that is a
missed prediction, and it was logged as one before it was investigated.

**It is not a miss, but the way it was stated was wrong.** Run 2's gates report for this cell reads
`status_counts: {'success': 144}`; run 3's reads `status_counts: {'success': 144}`. **Identical.** The
five are the fleet's long-known baseline — `la_rural` 5 plus `la_urban` 1 = **the 6 failures behind the
standing 8,154-of-8,160 fleet count.** They are unchanged by the OPEN-49 fix, as they must be: this cell
has zero Unknown buildings, so the OPEN-55 mechanism cannot reach it.

They are also a **visibly different failure class**:

| | OPEN-55 failures | `la_rural` baseline failures |
|---|---|---|
| error | `CalcHeatBalanceInsideSurf` runaway | `Temperature (high/low) out of bounds` |
| magnitude | 10⁵ – 10⁷ °C | −127 – +225 °C |
| population | `OpenUBEMUnknown` only | classified buildings |
| provenance | new in run 3 | present identically in run 2 |
| repair path | none attempted | zero-area strip, then reroute to `one_zone_per_floor` |

**What this corrects.** The model estimates **failures caused by the PDE draw**. It says nothing about
the pre-existing baseline, and §4A.1's phrasing — "expected failures" against a raw tolerance — silently
implied it did. The comparison against the drop tolerance must be
`baseline + mechanism-attributable`, not the mechanism term alone.

**Does any projection flip?** No. Measured per-cell baseline (run-2 result rows minus run-2 successes)
is **5 for `la_rural`, 1 for `la_urban`, and 0 for the other ten cells**. `la_rural` lands at 5 against a
tolerance of 5 — passing exactly at the boundary, which is what it did in both runs. `la_urban` lands at
about 2 against 6. **The five predicted stops and seven predicted passes are unchanged.**

**Kept as a standing caution.** A model that predicts one mechanism's failures must not be scored
against a cell's total failure count. `la_rural` is a correct prediction *of the mechanism* and would
have been recorded as a false one had the run 2 baseline not been checked.

---

### 4A.3 🔴 The model missed — `la_centre` stopped, and the dose-response curve is **not** transferable between cells

**Added 2026-08-18 20:12.** §4A.1 predicted `la_centre` would **pass** (3.9 expected against a tolerance
of 5) and flagged it as the marginal call. **It stopped:** `ZERO-FAIL: 10 failures exceed tolerance 5`.
**The prediction was wrong, and it was wrong in the unsafe direction — it under-predicted.**

All 10 failures are `OpenUBEMUnknown`; **no classified building failed**, so §3's central claim is
untouched. What breaks is the *quantitative* curve of §4A.

**Ten of the cell's fifteen Unknown buildings failed — 67 %.** Their drawn equipment densities:

| drawn equipment_w_m² | failed |
|---|---|
| 4934.8, 4847.0, 4292.5, 4096.3, 3468.6, 2967.1, 2813.3, 2206.6 | ✓ all |
| **1541.8** | **✓** |
| 1145.2 | ✗ |
| **708.7** | **✓** |
| 754.2, 521.1, 241.2, 30.0 | ✗ |

Two of these sit **below 1500 W/m²**, where the pooled NYC cells recorded **0 failures in 194
buildings** (rate exactly 0.000). And the ordering is not even monotonic within this cell — 708.7 failed
while 1145.2 survived.

**What this means.** The drawn equipment density is the *cause*, but it is **not a sufficient statistic
for the failure probability**. Susceptibility to heat-balance divergence clearly depends on properties
of the building the load lands on — zone volume, envelope area, storey count, installed capacity, and
plausibly climate, since `la_centre` runs a hot-dry Lancaster EPW against NYC's 4A. **The
per-bin rates fitted on two NYC cells do not transfer to a Los Angeles urban centre.**

⚠️ **What is *not* claimed:** no cause for `la_centre`'s higher susceptibility is asserted here. Two
NYC cells and one LA cell cannot separate climate from geometry from storey count. Recording the
candidates is not the same as choosing one, and choosing one on this evidence would be invention.

**Revised projection — stated as a bracket, not a point.** Rather than pretend to a curve that has just
been falsified, the remaining cells are bounded by the two observed regimes: the **NYC dose curve**
(lower) and **`la_centre`'s flat 67 % of all Unknowns** (upper).

| cell | Unknown | NYC-curve | la_centre-rate | tolerance | verdict |
|---|---|---|---|---|---|
| austin_centre | 37 | 14.4 | 24.7 | 5 | **STOP either way** |
| nyc_centre (T03 retry) | 35 | 10.7 | 23.3 | 7 | **STOP either way** |
| austin_suburban | 24 | 8.9 | 16.0 | 5 | **STOP either way** |
| austin_rural | 7 | 2.8 | 4.7 | 5 | passes either way (**upper bound is 4.7 vs 5 — close**) |
| austin_urban | 5 | 0.7 | 3.3 | 5 | passes either way |
| la_urban (T03 retry) | 2 | ~2 incl. baseline | ~2 | 6 | passes either way |

**Every remaining call is now bracket-robust** — each lands the same way under both regimes, with
`austin_rural` the only one close. That is a stronger position than the point estimate it replaces, and
it is *because* the point estimate failed.

**Running total: six of twelve cells stop** — `nyc_suburban`, `nyc_urban`, `la_centre` observed;
`austin_centre`, `austin_suburban`, `nyc_centre` predicted under both bounds. §4's original "four to
six" was right at its upper edge; §4A.1's narrowing to "five" was **too confident, and is withdrawn.**

**The ruling is unaffected** — as §4.1 said from the start, it never depended on the failure count.

---

### 4A.4 Two observations from `austin_rural`, one of which sharpens §4.1

**Added 2026-08-18 20:32.** `austin_rural` finished `rc=0` with **4 failures, all `OpenUBEMUnknown`**
(4 of its 7), against a predicted bracket of 2.8–4.7 and a tolerance of 5. **Inside the bracket, and the
verdict — pass — was right.** The bracket now stands at **2 hits, 0 misses**, against the point
estimate's 1 miss.

**(a) A hot/cold pattern, offered as a hypothesis and nothing more.** The share of Unknown buildings
that fail is not uniform across regions:

| region | cells observed | Unknown failing |
|---|---|---|
| NYC (CZ 4A) | 2 | 154 / 518 = **30 %** |
| LA (hot-dry) | 1 | 10 / 15 = **67 %** |
| Austin (hot-humid) | 1 | 4 / 7 = **57 %** |

The two hot-climate cells sit far above the two cold ones. That is **consistent with** cooling-dominated
climates being less able to reject a large internal gain — but it is four cells, the Austin and LA
samples are 7 and 15 buildings, and region is fully confounded with building stock, storey count and
geometry. ⚠️ **This is a hypothesis to test if anyone ever needs the failure rate predicted, not a
finding.** It plays no part in the ruling.

**(b) 🔴 The drop is selective, so a passing cell is not merely contaminated — it is *biased*.**
This sharpens §4.1. `austin_rural` passed by **dropping 4 of its 7 Unknown buildings**, and the four
dropped are precisely those that drew the most extreme equipment loads. What remains is the low-draw
tail of an already-distorted distribution.

So the drop-tolerance gate does not clean a cell. It **removes the buildings whose draws were most
absurd and keeps the rest**, which means a passing cell's EUI is distorted twice over, in opposite
directions:

- **upward**, by surviving Unknown buildings carrying implausibly large equipment loads;
- **and by non-random deletion**, because the buildings removed were not a random sample — they were
  the extreme tail.

Neither distortion is quantifiable from run 3, and they do not cancel. **A cell that passed the gate is
not evidence that the cell is sound**, and `austin_rural` — which lost 57 % of its Unknown population to
reach `rc=0` — is the clearest illustration in the run.

---

### 4A.5 🔴 `austin_centre` — the prediction held, and a transport failure was hiding a model failure

`austin_centre` returned **`rc=1`** at 20:37:49 after 55 minutes. On the return code alone it belongs
with `nyc_centre` and `la_urban` in the transport column. It does not. The zero-fail gate had already
fired 468 log lines before the traceback:

```
austin_centre.log:1602   ZERO-FAIL violation: 20 failed buildings.
austin_centre.log:2070   Attempting zero-surface-area repair on 20 failed buildings...
austin_centre.log:2213   subprocess.TimeoutExpired  (v12_cell_pipeline.py:334, sacct)
```

The cell simulated 413 buildings, 37 of them Unknown, and **20 failed** against a tolerance of
`max(5, 1% x 413) = 5`. The pipeline then tried to repair them, submitted reroute array `1274797`,
and died reading `sacct` — the same timeout axis as `la_urban`, one line further down (`:334` vs
`:327`). The `rc=1` is real, but it is the *second* failure of the cell, not the first.

**Why 20 is a STOP even though the repair result was never read.** The repair stage's yield is now
measured across every cell in this run that reached it:

| cell | pre-repair | post-repair | recovered |
|---|---|---|---|
| `nyc_rural` | 3 | 3 | 0 |
| `austin_rural` | 4 | 4 | 0 |
| `la_rural` | 7 | 5 | 2 |
| `la_centre` | 11 | 10 | 1 |
| `nyc_suburban` | 73 | 71 | 2 |
| `nyc_urban` | 83 | 83 | 0 |

**The maximum recovery observed in six cells is 2 buildings.** For `austin_centre` to have landed at
or under its tolerance of 5 the repair would have had to recover 15. That is not a close call, and it
does not depend on assuming the repair failed — it holds at three times the best yield ever seen here.
`austin_centre` is a model stop. The transport failure only prevented it from being *labelled* one.

**Prediction outcome.** `austin_centre` was pre-registered as **STOP**, bracket **14.4-24.7** failures.
Observed **20**. Correct on the direction, and inside the bracket. Scoreboard: **8 correct, 1 missed**;
bracket **3 hits, 0 misses**. The bracket of §4A.3 — adopted only after the point estimate failed on
`la_centre` — has now been tested three times without a miss, on cells spanning 226 to 1,779 buildings.

**`austin_suburban` re-reads the same way.** Its log carries `ZERO-FAIL violation: 14 failed buildings`
at line 1438 and its repair attempt at 1767, before it died at `:536`. Tolerance is
`max(5, 1% x 437) = 5`. Recovering 14 down to 5 requires 9, against a measured ceiling of 2. It is a
model stop on the same evidence, one step less direct than `austin_centre` because its manifest was
never written.

#### The consequence for this run's arithmetic

The tally of stopping cells was six. With `austin_centre` and `austin_suburban` re-classified it is
**five of twelve** *(corrected in §4A.6 — first written as eight)*, and only two cells — `nyc_centre` (died at `:265`, before any simulation) and
`la_urban` (died at `:327`, before the gate) — are transport failures with no model verdict attached.

| classification | cells |
|---|---|
| passed the gate | `nyc_rural`, `la_suburban`, `la_rural`, `austin_rural` |
| stopped, labelled `rc=2` | `nyc_suburban` (71), `nyc_urban` (83), `la_centre` (10) |
| stopped, mislabelled `rc=1` | `austin_centre` (20), `austin_suburban` (14) |
| transport only, no verdict | `nyc_centre`, `la_urban` |
| still running | `austin_urban` |

#### 🔴 The methodological point, which outlasts this run

**A return code is not a classification.** Two of the three cells I had filed as transport failures
were carrying an unread model verdict, and the only reason it was recoverable is that the gate prints
its count to the log before the repair stage runs. Had the timeout landed one stage earlier, those
twenty failures would have left no trace at all, and this investigation would have reported six
stopping cells instead of eight — an undercount of a third, in the direction that makes the defect
look smaller.

This is a specific instance of the general rule in §4.1: what a cell *reports* is downstream of where
it happened to die. It is also why the OPEN-54 remedy is not a tidiness fix. An unchecked exit status
does not merely cost a rerun; it silently reassigns cells from one finding to another, and the
reassignment always runs toward the benign reading, because a crash truncates evidence rather than
inventing it. See [OPEN-54 §3.4](INVESTIGATION_open-54_ssh-unchecked-exit.md).

### 4A.6 `austin_urban` — twelve of twelve landed, a bracket miss, and a correction to my own count

`austin_urban` finished at 20:47 with **`DROPPED 5 buildings (<= tolerance 5)`**. It passed. It passed
by exactly zero margin, and it passed by deleting **every Unknown building it had**.

```
austin_urban:  425 buildings,  5 Unknown,  5 failed,  tolerance 5  ->  PASS
```

The five dropped rows are the five Unknowns, and their error text is the same runaway as everywhere
else — `way/381805728` reached **5,381,322.93 °C**, which is the `LargeDataCenterHighITE` bound
(5381.96 W/m²) showing up in the temperature field almost digit for digit.

#### The bracket missed, and it missed in the unsafe direction

`austin_urban` was pre-registered as **pass, 0.7–3.3 failures**. It produced **5**. The direction was
right; the count was not. Corrected scoreboard:

| axis | result |
|---|---|
| direction (pass / stop) | **9 correct, 1 missed** (`la_centre`) |
| failure-count bracket | **3 hits, 1 miss** (`austin_urban`) |

Both bracket-relevant misses run the same way — **more failures than predicted, never fewer** — and both
are on cells with very few Unknowns: `la_centre` (15) and `austin_urban` (5). The three brackets that
held were on cells with 7, 24 and 37 Unknowns. **The bracket is reliable where the Unknown count is
large enough for a rate to mean anything, and it under-predicts where it is not.** That is the honest
statement of its range of validity, and it was not part of the model as originally written.

#### 🔴 The sharpest case yet for §4A.4(b)

`austin_urban` is the cleanest example in the run of what "passing the gate" is actually worth:

> **A cell with 5 Unknown buildings had all 5 fail, dropped all 5, and was recorded as a clean pass.**

Its reported EUI is computed over 420 buildings from which **100 % of the unnamed buildings have been
removed** — not a random 5, but precisely the ones the defect touched. `la_suburban` is the mirror
image: 2 Unknowns, both survived, both carrying whatever load they drew, and its EUI includes them.
**Two cells in the same run, both recorded as passes, distorted in opposite directions.** Neither
distortion is quantifiable from the artifacts, and pooling them does not cancel it.

#### ⚠️ Correction — the number of stopping cells is five, not eight

I wrote "eight of twelve cells stop" into the register, the prompt and the plan log after
`austin_centre`. **That was wrong.** With all twelve landed the measured count is:

| outcome | count | cells |
|---|---:|---|
| **stopped** (failures > tolerance) | **5** | `nyc_suburban` 71/16 · `nyc_urban` 83/18 · `la_centre` 10/5 · `austin_centre` 20/5 · `austin_suburban` 14/5 |
| passed | 5 | `nyc_rural` 3/5 · `la_rural` 5/5 · `la_suburban` 0/13 · `austin_rural` 4/5 · `austin_urban` 5/5 |
| no verdict (transport) | 2 | `nyc_centre` · `la_urban` |

Five, not eight. The error was mine in the arithmetic, not in the evidence — I carried the two
re-classified `rc=1` cells forward as *additions* to a total that had already been revised upward once
for predicted stops, and double-counted them. **The conclusion it was offered in support of does not
change**, and that is worth stating precisely so the correction is not read as bigger than it is:

- **T04 is still unreachable.** Five cells produced no results at all.
- **The five passes are still not poolable**, for the reason in §4A.4(b) and above — four of the five
  passed *by dropping the affected buildings*, at rates of 3/5, 5/5, 4/5 and 5/5 of tolerance, and
  `la_suburban` passed by retaining them.
- **Four of the five passes sit at or within two of their tolerance.** Nothing here is comfortable.

The count was load-bearing for none of that. It was still wrong, and it is corrected everywhere it
was written.

## 5. What this does *not* say

- **It does not invalidate the OPEN-49 diagnosis.** Cell-dependent bounds were a real defect and route 2
  correctly removed the dependency. The error is in *what* replaced it, not in removing it.
- **It does not indict route 1** (`_per_building_rng`). Per-building keying is correct and is what made
  this diagnosis possible at all — the draws could be regenerated exactly.
- **It does not implicate the adopted `phaseE_elevrb` run or run 2.** Both predate the fix and used
  cell-local bounds. The published `157.1` is not affected by this defect.
- **It is not a cluster or infrastructure fault.** Distinct from OPEN-54 in every respect; the two failed
  cells in this run failed for unrelated reasons.

---

## 6. Why the run was allowed to continue

Stopping would have saved cluster time that is otherwise idle and disk that is not scarce
(6.3 T used of a 9.8 T warn; the whole `fleets` tree is 2.0 T). It would have cost the one thing worth
having: **an observed per-cell failure census instead of an estimated one.** §4's table is a projection
from a single calibration point; letting the remaining cells run converts it to measurement.

The ruling does not change either way — run 3 cannot yield a publishable fleet number, and that was
already certain once the mechanism was proven. So the run continues for evidence, not for its headline.

⚠️ **`open48_refleet3` results must not be read as a fleet.** Cells that complete carry Unknown
buildings with data-centre equipment loads. This document is the warning label.

---

## 7. Remedy — specified, deliberately not applied

The bound must be **physically screened**, not merely made cell-independent. Three options, in
increasing order of how much they change:

1. **Exclude implausible donors from the Unknown PDE table.** The four data-centre archetypes are not
   credible donors for a building whose type is unknown; nor, arguably, is `Laboratory`. A fixed
   exclusion list keeps route 2's cell-independence while restoring a physical range.
2. **Draw from a percentile range** (e.g. p5–p95 of the full table) rather than min/max, so a single
   extreme archetype cannot set the bound.
3. **Screen the drawn value**, clipping equipment density to a defensible ceiling for an unknown
   building.

Option 1 is the narrowest and most defensible: it names the assumption, keeps the fix's intent intact,
and is auditable. **The choice is a DESIGN question and is not the director's to make unilaterally** —
it changes what an Unknown building *is*, which is a modelling commitment, not a bug fix.

**Nothing is applied now.** Editing `openubem/semantic/` mid-run would break the single-variable
comparison run 3 exists to make, exactly as editing the pipeline would have (OPEN-54 §6). The order is:
finish run 3, rule on it, then fix this.

---

## 8. Disposition

- Registered as **OPEN-55**. It is a repository defect and it outlives this run.
- **`nyc_suburban` is not a T03 retry candidate.** The draw is deterministic; a retry reproduces the
  identical 71 failures. This is the operational difference from OPEN-54's `nyc_centre`, which was
  transient and *is* a retry candidate.
- OPEN-49 **cannot close** while this stands. Its mechanism fix is sound; its route-2 implementation
  introduced this. The two must be resolved together.
- The CP-2 ruling on whether the published `157.1` moves is now effectively determined: **it does not
  move on run 3's evidence.** Reasoning is written up at CP-2, not here.
