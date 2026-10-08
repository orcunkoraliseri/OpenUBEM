# MEASUREMENT — OPEN-09: is "cosmetic" true?

> Task **C06** of `PLAN_compute-queue.md`. Written 2026-08-06. No new EnergyPlus runs —
> pure re-analysis of a pre-existing, already-audited matched-control population.

## 1. Cost gate (mandatory first step, answered before any analysis)

**Population identified:** F11-N / F11-N-b from the closed E-LA-20 multilayer-fix arc
(`docs_DONE/SETUP/layoutAssigner/DONE/e-la-20/DONE-PLAN_e-la-20_multilayer-fix.md:1193-1259`).
150 real `nyc_rural`/`SmallOffice` buildings, built through the shipped `layout_assign`
production path, run twice each — once `thermal_mass=True` (F11-N), once
`thermal_mass=False` (F11-N-b, matched control) — same buildings, same geometry, same
weather, same schedules, one variable. This is exactly the population OPEN-09's own
carried 96/150 vs 8/150 figures came from.

**Runs on disk, verified directly (not from any manifest):**
- `scratchpad/e-la-20-fix/f11n_work/runs/` — 150 directories, each with a full raw
  EnergyPlus output set (`eplusout.err`, `.eio`, `.sql`, `eplustbl.htm`, `.end`, …).
- `scratchpad/e-la-20-fix/f11nb_work/runs/` — 150 directories, identical `osm_id` set
  (diffed, identical).

**Verdict: (i) the runs exist.** This was a pure analysis task. No EnergyPlus was
launched, no cluster or Speed access, no new local run. 0 of the 400-simulation gate
was used.

## 2. Method

The open part of OPEN-09 is: *compare EUI on converged vs non-converged runs of the
same buildings.* Both raw `.err`/`eplustbl.htm` sets were re-read directly (never a
pre-computed CSV column) for all 150 × 2 = 300 run directories:

1. **Convergence status, per building, under `thermal_mass=True`** — grepped directly
   from `f11n_work/runs/<id>/eplusout.err` for
   `CheckWarmupConvergence: Loads Initialization ... did not converge after 25 warmup
   days`. A building is "non-converged" if that line appears ≥1 time, "converged" if 0.
   This column does not exist in the prior F11-N CSV (it only recorded `ctf_severe_present`)
   — it was re-derived fresh from the raw `.err` text for this task.
2. **EUI, both arms** — parsed directly from each run's own `eplustbl.htm`, "Total Site
   Energy" table row (same regex the original F11-N/F11-N-b harnesses used:
   `Total Site Energy</td>...<td>...</td><td>([\d.]+)</td>`, MJ/m² → kWh/m²). Not
   reimplemented — same EnergyPlus-native summary table, same extraction logic as the
   already-audited artifacts.
3. **Fatal check, both arms** — the two-space regex `\*\*\s+Fatal\s+\*\*` (C07's fix),
   applied to all 300 `.err` files directly.
4. **`pct_delta = (EUI_true − EUI_false) / EUI_false × 100`** per building, then split
   into the non-converged (96) and converged (54) groups by step 1's flag.

No sampling, no cap, no truncation: **all 150 buildings, both arms, 300 raw output
directories read in full.**

Script: `c06_analysis.py` + `c06_stats.py`, session scratchpad only, not committed
under `docs/`. Output artifact:
`openubem/outputs/comparisons/c06_open09_converged_vs_nonconverged_eui.csv` (150 rows).
Figure: `openubem/outputs/c06_open09_converged_vs_nonconverged_eui_delta.png`, mirrored
alongside this document.

## 3. Reconciliation and sanity checks

- 150 directories in `f11n_work/runs/`, 150 in `f11nb_work/runs/`, identical `osm_id`
  sets (`diff` clean).
- 0 missing `.err`, 0 missing `eplustbl.htm` across all 300 run directories.
- Fatal count, both arms: **0/150 in each** (two-space regex) — consistent with the
  arc's own closing audit (CTF Fatal count 0/150, both arms).
- Non-converged count reproduces exactly: **96/150 (64.0%)** under `thermal_mass=True`,
  **8/150 (5.3%)** under `thermal_mass=False` — matches the register's carried figures
  and F11-N-b's audited numbers exactly, independently re-derived from raw text, not
  read off a CSV column.
- All-150 `pct_delta` distribution reproduces F11-N-b's audited numbers to 3 decimal
  places (min −2.124, p25 −1.925, median −1.732, p75 −1.535, max −0.995, mean −1.716) —
  confirms this re-derivation pipeline agrees with the prior, already-audited artifact
  before any new split is drawn from it.

## 4. Result — EUI delta distribution, split by convergence status

`pct_delta = (EUI[thermal_mass=True] − EUI[thermal_mass=False]) / EUI[thermal_mass=False] × 100`,
same building both arms.

| group | n | min | p25 | median | p75 | max | mean | stdev |
|---|---|---|---|---|---|---|---|---|
| **Non-converged** (≥1 warmup severe under True) | 96 | −2.0685 | −1.8718 | −1.6290 | −1.4305 | −0.9946 | **−1.6375** | 0.2671 |
| **Converged** (0 warmup severes under True) | 54 | −2.1239 | −2.0121 | −1.8770 | −1.7370 | −1.1595 | **−1.8550** | 0.1897 |
| All 150 (sanity check) | 150 | −2.1239 | −1.9246 | −1.7317 | −1.5354 | −0.9946 | −1.7158 | 0.2637 |

**Both groups are tightly one-directional** — every one of the 150 deltas is negative
(the mass roof consistently lowers site EUI vs the no-mass control, as the E-LA-20 arc
already established). **96.3% of the converged group's deltas fall inside the
non-converged group's own [min, max] range** — the two distributions overlap almost
completely; there is no outlier, no sign flip, no erratic value in either group.

**The group means do differ, and the difference is statistically real:**
mean(non-converged) − mean(converged) = **+0.2176 percentage points** (non-converged is
*smaller* in magnitude, not larger). Welch t-test t=5.75, p=5.3×10⁻⁸; Mann-Whitney
p=4.1×10⁻⁷. Spearman correlation between per-building warmup-severe-count (0–5) and
`pct_delta`: ρ=+0.430, p<10⁻⁶ — monotonic and in the same direction (more warmup
severes → smaller-magnitude, i.e. less negative, delta).

**In absolute terms this gap is small.** 0.22 percentage points at the population's
median true-arm EUI (91.19 kWh/m²) is **≈0.20 kWh/m²** — a fraction of a percent of
the building's own annual EUI, not a materially different result.

## 5. Verdict

**"Cosmetic" is earned, not merely inherited, with one nuance now on the record.**

- **No evidence of the alarming failure mode.** If warmup non-convergence were
  corrupting the annual result, the non-converged group would show larger-magnitude,
  more scattered, or sign-inconsistent deltas than the converged group. It shows the
  opposite: tighter concentration around a *smaller* magnitude, and 96% range overlap.
  A reader relying on a non-converged run's EUI is not getting an outlier or an
  unreliable number relative to a converged run of the same building.
- **But the two groups are not statistically indistinguishable**, and it would be
  overclaiming to say so. There is a real, monotonic, ~0.22-percentage-point
  relationship between warmup-convergence difficulty and delta magnitude — small in
  absolute EUI terms (≈0.2 kWh/m² at the median), but detectable at n=150 because the
  within-group spread is tight (stdev 0.19–0.27 pp).
- **Net disposition:** the five inherited log entries (E-LA-14, E-LA-16, E-LA-18,
  E-LA-19, E-LA-23) do **not** need correcting on the "cosmetic" claim's substance —
  the claim, now actually tested, holds at the population it was ever measured on. What
  changes is only the epistemic status: "cosmetic" moves from *inherited across five
  entries, never tested* to *tested once, on the E-LA-20/23 matched-control population,
  and confirmed with a quantified, small, correctly-signed residual correlation.* It
  has not been tested outside this one archetype/cell/roof-assembly combination, and
  that scope limit should travel with the claim from here on.

## 6. What this does NOT do

- Does not settle consequence (a) of OPEN-09 — the ≈299/8,160 ≈ 3.66% fleet
  projection remains a projection, out of scope here as the plan specifies.
- Does not generalize "cosmetic" beyond `nyc_rural`/`SmallOffice`/`u_roof=0.119` — this
  is the only population where a matched thermal_mass control has ever been run.
- Does not re-run or touch E02 or any cluster resource; entirely local, read-only
  re-analysis of a closed arc's own artifacts.
