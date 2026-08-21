# MEASUREMENT — untrimmed `layout_assign`: a 48-building sample at HEAD

**Date:** 2026-08-19 (late) · **Plan:** `implemenation/previous/PLAN_layout-assign-untrimmed-2026-08-19.md` (T01–T04, CP-1)
**Items touched:** OPEN-03 (cross-mode gap), OPEN-18 (vertical-form distortion), OPEN-10 (floor-area denominator)
**Author:** director. T01/T02 executed by a Sonnet executor; T03/T04 computed by the director from the
executor's tables after the executor stalled without writing up (see §8).

> **This is a 48-building sample and every number below is a sample number.** It is not a fleet
> figure and no fleet figure may be derived from it. The adopted fleet result — **153.8231 kWh/m²
> pooled** (total simulated energy ÷ total simulated floor area) over **8,153** buildings /
> **24,320,582 m²** — is untouched by this measurement and appears here only as context.

🔴 **CORRECTED 2026-08-19 (same night) — read §10 before quoting any number from §3, §4 or §6.**
The gap reported in those sections is overstated: the parser figure they rest on undercounts
lighting and equipment wherever a zone multiplier is in play. Corrected: pooled **−11.26 %**,
median **−17.72 %**, and **≈−24 %** on the cleanest subset. The finding survives; its size changed.
**No adopted figure is affected — the artifact cannot reach `auto`.**

## 1. What was run

48 buildings: 4 per cell × 12 cells, at the 10th/35th/65th/90th percentile positions of
`footprint_area_m2` among run-4 `simulation_status == success` buildings (integer index, stable
mergesort, no RNG). Each was rebuilt in `layout_assign` with **`trim_outputs=False`**, simulated
locally in its own isolated `run_dir` (OPEN-58 guard), and parsed with the production
`parse_building()`. Fixtures: `open48_refleet4` — the same generation the adopted figure comes from.
Comparison side: that generation's `auto` `05_results.csv`, joined on `osm_id`.

Script: `scripts/analysis/open03_untrimmed_layout_assign_sample_2026-08-19.py`
Tables: `openubem/outputs/comparisons/open03_untrimmed_sample_eui.csv`, `..._join.csv`

## 2. T02 — the capability defect is confirmed cured, 48/48

**All 48 parsed `success`. Zero build failures, zero simulation failures, zero parse failures.**

This is the headline. Every `layout_assign` build in this arc until now used `trim_outputs=True`,
which skips the per-zone `Output:Variable` block, and the parser's integrity gate
(`openubem/results/parser.py:203`, `layout_assign` branch `:221-236`) then returns
`failed_zone_mismatch`. T18 showed the cure on one building; this shows it holds across 12 cells,
9 archetypes, 1–18 storeys and 1–90 zones. **OPEN-03's measurement-capability defect is settled:
`trim_outputs=False` is the whole fix, and nothing else blocks `layout_assign` from yielding EUI.**

Zone counts behave as the archetype implies and are stable within an archetype: SmallOffice 6,
MidriseApartment 27, MediumOffice 18, LargeOffice 23, LargeHotel 22, Warehouse 3, RetailStandalone 5,
Courthouse 81–90, `OpenUBEMUnknown` 1–2.

## 3. T03(a),(b) — the cross-mode gap, sample only

| weighting | layout_assign | auto | gap |
|---|---|---|---|
| pooled, n=48 (Σ energy ÷ Σ floor area, both sides, same buildings) | 108.64 | 147.30 | **−26.25 %** |
| median per building, n=48 | — | — | **−24.40 %** |

Mean per building −23.02 %. Range −44.71 % to **+2.67 %** — and that single positive value
(`austin_rural way/1165379866`, RetailStandalone) is the **only** building of the 48 where
`layout_assign` came out above `auto`. Pooled and median agree in sign and are within 2 points of
each other, so unlike OPEN-59 there is no weighting disagreement to adjudicate here.

**`layout_assign` runs systematically about a quarter below `auto` on this sample.** That is a large,
one-directional difference between two modes that are supposed to describe the same buildings, and it
is the first HEAD-consistent, generation-clean measurement of it this arc has had.

## 4. T03(c) — the floor-area confounder does not explain the gap

27 of the 48 disagree on floor area between the two modes by more than 10 % (OPEN-10, flagged by T18).
Splitting on that:

| subset | n | pooled gap | median gap |
|---|---|---|---|
| floor area agrees within 10 % | 21 | −19.73 % | −25.87 % |
| floor area disagrees by >10 % | 27 | −32.57 % | −24.29 % |

**The gap survives in the clean subset.** The pooled −19.73 % is however 75 % carried by one building
(`la_centre way/425993511`, Courthouse, 88,309 m², gap −15.84 %); excluding it, the remaining 20
area-agreeing buildings pool to **−28.02 %** with a median of **−26.05 %**. So on the subset where the
denominator is not in question, the gap is roughly **−20 % to −28 %** depending on weighting, and the
median sits at about **−26 %** in every cut.

**Conclusion for OPEN-03: the denominator mismatch inflates the raw gap but is not its cause.** A real
energy-side difference of order −25 % remains after the confounder is removed. This needs its own
investigation — it is not settled by this measurement.

## 5. T03(d) — disk cost of running untrimmed

`.sql` size across the 48: mean **20.0 MB**, median **8.1 MB**, min 2.4 MB, max **124.9 MB**
(the 90-zone Courthouse). Sample total 0.94 GB. Size tracks zone count at about **1.40 MB per zone**.

Extrapolated to a full fleet of 8,160 buildings: **≈159 GB** at the sample mean, **≈995 GB** if every
building were as large as the worst case. The register records untrimmed `fast_zone` city passes
exceeding 800 GB, so the mean-based ≈159 GB is the credible planning number and the archetype mix
drives it.

**A full-fleet untrimmed run is affordable on disk at roughly 160 GB.** That is a decision for the
user, not a recommendation taken here.

## 6. T04 — OPEN-18's slice: small buildings in cold cells

The slice is the 10th/35th percentile slots of the four NYC cells: **n = 8**.

| slice | n | pooled gap | median gap |
|---|---|---|---|
| NYC, small (slots 10/35) | **8** | −27.98 % | −26.36 % |
| rest of sample | 40 | −25.00 % | −24.31 % |

Per-building gaps in the n=8 slice: −27.5, −26.1, −36.7, −36.8, −13.8, −12.2, −12.4, −26.7 %.

**At n = 8 the slice runs about 3 points below the rest of the sample, and the slice's internal spread
(−12 % to −37 %) is far wider than that 3-point difference.** This does not support a claim that
OPEN-18's vertical-form distortion bites measurably harder on small buildings in cold cells — the
separation is well inside the noise at this n. It does not refute it either. **OPEN-18 is not sized by
this measurement; it would need a purpose-built sample with many more small cold-cell buildings.**

## 7. Secondary observation, not a task

Median gap by archetype (n in brackets): MidriseApartment −12.6 (9), `OpenUBEMUnknown` −12.5 (3),
Warehouse −17.6 (1), Courthouse −20.3 (2), LargeHotel −26.1 (1), SmallOffice −26.1 (26),
LargeOffice −29.5 (3), MediumOffice −34.9 (2), RetailStandalone +2.7 (1).

The gap is not uniform across archetypes — office types run roughly twice as far below `auto` as
MidriseApartment does. Most cells are dominated by SmallOffice (26 of 48), so the sample's headline
number is largely a SmallOffice number. **Recorded as a lead for whoever investigates §4, not as a
finding.**

## 8. Deviations

1. **The executor stalled after launching T02** and reported "waiting for the run to finish" without
   writing the report or any progress-log entry; its output file is 0 bytes. The run itself completed
   normally (48/48). The director verified disk state directly, waited on a completion detector, and
   performed T03/T04 and this write-up. Known failure mode — `feedback_executors_stall_waiting_on_monitors.md`.
2. **An undocumented smoke gate exists in the script** (`OPEN03_SMOKE_SLOTS` env var, lines 89–92)
   which filters the sample to selected percentile slots. The plan did not specify it. It was used for
   a 1-building smoke before the full run and was not set for the full run — the final tables carry all
   48 rows. Benign, but it was an unpinned addition.
3. **No run log was redirected to disk**, so the T02 wall-clock and any EnergyPlus warnings are not
   recoverable. State was reconstructed from the tables and the scratchpad tree.
4. Every pinned §4 decision was checked in the script and holds: `trim_outputs=False`,
   `resolution_mode="layout_assign"`, deterministic percentile index, per-building `run_dir`,
   `n_jobs=4`, run-4 fixtures, `auto` join on `osm_id`.

## 9. What this changes, and what it does not

- **Changes nothing about any published number.** OPEN-32 already bounds the effect on adopted
  results at zero; this measurement is consistent with that and does not touch 153.8231.
- **Settles the capability question** behind OPEN-03: untrimmed `layout_assign` parses, 48/48.
- **Opens a real question**: a systematic ≈25 % cross-mode energy difference that survives the
  floor-area confounder. Nothing in this arc explains it yet.
- **Does not size OPEN-18.** n=8 is too small; that is the honest answer.


---

## 10. 🔴 CORRECTION — 2026-08-19, same night, by the director

**§3, §4 and §6 above overstate the gap. The numbers below supersede them.** The finding survives;
its size does not. This correction was produced by the follow-on plan
(`implemenation/previous/PLAN_gap-decomposition-2026-08-19.md`, T01) and re-derived independently by the
director before being applied.

### What was wrong

`total_eui_kwh_m2` — the parser figure §3 was built on — **undercounts lighting and interior
equipment whenever a zone carries a multiplier greater than 1.** Those two end uses are summed from
per-zone hourly variables, which EnergyPlus does *not* scale by the zone multiplier, while the floor
area they are divided by **is** multiplier-aware (`openubem/results/parser.py:431-433`,
`resolve_simulated_floor_area()`). Every other end use — cooling, heating, fans, pumps, hot water —
matches the multiplier-correct ABUPS table to <0.01 %.

**42 of the 48 are affected.** Only **6 of 48** reconcile against the ABUPS total within 2 %.
Reconciliation error: median **4.71 %**, mean 17.56 %, 90th percentile 24.19 %, max **192.28 %**;
**14 buildings exceed 10 %**.

🔴 **The production code already contains the gate that catches this** —
`check_building_integrity()` (`openubem/results/parser.py:602-646`) returns `abups_ok=False` for the
worst offender. **The pipeline that produced these tables never calls it.** Several `scripts/run_*.py`
entry points do; the fleet path does not.

### Does this touch the adopted fleet figure? No — verified, not assumed

**Zone multipliers are written in exactly one place: `openubem/geometry/layout_assigner.py`**
(`match_storeys()`, `z_obj.Multiplier = residual_multiplier` at `:649`). No other module in
`openubem/` writes one. The director inspected three `auto`-mode fleet IDFs from run 4 directly
(`…/open48_refleet4/nyc_rural/fleet_staging/idfs/`): **every `Multiplier` field is 1**.
**The artifact cannot reach `auto`. `153.8231 kWh/m²` pooled over 8,153 buildings is untouched.**
What it does mean is that **every `layout_assign` EUI this project has ever recorded is undercounted**
by this mechanism — a `layout_assign`-only defect, in a mode not on the production path.

### The corrected sample numbers (n=48, multiplier-correct via ABUPS totals)

| cut | as published in §3–§6 | **corrected** |
|---|---|---|
| all 48, pooled | −26.25 % | **−11.26 %** |
| all 48, median | −24.40 % | **−17.72 %** |
| area agrees ≤10 %, n=21, pooled | −19.73 % | **−17.39 %** |
| area agrees ≤10 %, n=21, median | −25.87 % | **−22.60 %** |
| area agrees, excl. the dominant Courthouse, n=20, pooled | −28.02 % | **−23.93 %** |
| area agrees, excl. Courthouse, n=20, median | −26.05 % | **−23.19 %** |
| NYC small slice, n=8, median | −26.36 % | **−18.48 %** |
| buildings above `auto` | 1 of 48 | **8 of 48** |

**What still stands.** A real, one-directional cross-mode difference, and it still survives the
floor-area confounder: on the 20 area-agreeing buildings excluding the Courthouse it is
**≈−24 %**. §4's conclusion — *the denominator mismatch inflates the gap but is not its cause* —
**holds, and is if anything cleaner now**, since the published and corrected figures agree most
closely on exactly that subset.

**What does not stand.** The headline "about a quarter below" is only true of the cleanest subset,
not of the sample as a whole; **pooled over all 48 the gap is −11 %, less than half what §3 reported**.
The pooled figure moves furthest because the correction is largest on a few big-area buildings.
**Pooled and median no longer agree within 2 points** (−11.3 vs −17.7), so §3's claim that there is
no weighting disagreement to adjudicate is **withdrawn** — there is one, and the median is the more
robust of the two here.

### Consequence for OPEN-03's attribution — the follow-on task's refutation is itself withdrawn

T01 concluded that vintage-correcting lighting+equipment could move total energy by at most
**7.76 %** (6.13 % for offices), and called that "well short" of half the gap — **but it measured
that against the uncorrected ≈25 % gap.** Against the **corrected** median gap of **17.72 %**, half
is 8.9 points and the maximum available is 7.76 points — **close enough that OPEN-03's "roughly half"
is no longer contradicted.** Against the area-agreeing-excluding-Courthouse cut (−23.9 %) it still
falls short. **The honest verdict is inconclusive, not refuted**, and the register records it that way.

### End-use shape (n=48, from ABUPS, unaffected by the correction)

Interior Equipment 32.45 %, Fans 21.17 %, Cooling 15.63 %, Interior Lighting 13.86 %, Heating 9.09 %,
Water Systems 7.08 %, Pumps 0.73 %. Lighting+Equipment together **46.31 %**. MidriseApartment (n=9)
41.21 % vs offices (n=31) 57.30 % — and MidriseApartment is dominated by hot water (37.93 %), a
different mechanism from the vintage-loads claim. These shares are internally consistent and do not
depend on the failed reconciliation.
