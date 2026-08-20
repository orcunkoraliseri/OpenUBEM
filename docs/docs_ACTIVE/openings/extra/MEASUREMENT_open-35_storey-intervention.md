# MEASUREMENT — OPEN-35: an intervention with a control on the storey-count contradiction

T04 of `implemenation/previous/PLAN_ten-items-2026-08-19.md`. Corpus: `open48_refleet` (run 2), the
same corpus `open35_eui_consequence.csv` and T07 used, and **not** `open48_refleet3` (T02 is
using that corpus concurrently this pass). `resolution_mode="auto"` throughout (production
default; what `v12_cell_pipeline.run_cell` uses with no override).

## 1. Census phase — discovered before any EnergyPlus compute, changes the plan's sample

The plan's step 1 says to sample from "the 1,031 buildings given a mid- or high-rise
archetype and built as a single storey." Before drawing a sample and spending EnergyPlus
compute, this task first recovered — by calling `_impute_levels()` directly, code-reused, not
reimplemented, with the exact `levels_group_median`/`levels_global_median` lookup step2
built for each of the 7 cells that contain this population — the storey count that actually
drove archetype selection for **every one of the 1,031 buildings**, not a sample of them
(cheap: no IDF is built in this phase).

**Result: the register's "chosen as though a 19-storey building, built as a 1-storey building"
framing describes a small minority of the 1,031, not the whole population.** Breakdown:

| cell | n | recovered levels | source | genuine disagreement? |
|---|---:|---:|---|---|
| `nyc_suburban` | 979 | 1 | `LEVELS_DEFAULT_LOW` (cell has **zero** observed-levels rows anywhere) | NO |
| `nyc_rural` | 22 | 1 | `LEVELS_DEFAULT_LOW` (cell has **zero** observed-levels rows anywhere) | NO |
| `austin_rural` | 18 | 1 | `GROUPMEDIAN_LEVELS_MED` (a real median, computed from real data, that happens to equal 1) | NO |
| `austin_suburban` | 1 | 1 | `GROUPMEDIAN_LEVELS_MED` (real median = 1) | NO |
| `nyc_urban` | 5 | 6 | `GROUPMEDIAN_LEVELS_MED` | **YES** |
| `la_urban` | 3 | 7 | `GROUPMEDIAN_LEVELS_MED` | **YES** |
| `austin_centre` | 3 | 45 | `GROUPMEDIAN_LEVELS_MED` | **YES** |

**1,020 / 1,031 (98.9%) are zero-disagreement**: `_impute_levels()` and `derive_num_floors()`
land on the *same* value (1) for these buildings, via different code paths that happen to
coincide — either because the whole cell has no ground-truth `levels` data to compute a
median from at all (`nyc_suburban` + `nyc_rural`, 1,001 buildings, 97.1% of the population on
their own), or because the group median genuinely computes to 1 (`austin_rural` +
`austin_suburban`, 19 buildings). **Only 11 / 1,031 (1.07%) — 3 cells, 3 archetypes-worth of
data — carry a genuine numeric disagreement** between the two fallbacks.

This does not contradict OPEN-35's mechanism (the two code paths **are** different and **can**
disagree — DESIGN fact, still true) or the population count (1,031 buildings **are** given a
mid/high archetype and built at one storey — still true, re-derived exactly). It corrects a
specific, previously-unmeasured claim about *why*: for 98.9% of this population, `MidriseApartment`/
`HighriseApartment` is being selected by a use-tag rule that does not require the imputed level to
exceed 1 (apartment tag -> apartment archetype, independent of the numeric fallback), not because
the archetype stage assumed a taller building than the geometry stage built. The archetype label
itself still *implies* more than one storey by name, and the building is still built at one — that
categorical mismatch is real and matches the register's count — but the "different numbers were
used" story only holds for the 11.

**Evidence:** `openubem/outputs/comparisons/open35_storey_intervention_census.csv` (1,031 rows).

## 2. Sample actually run

Given the above, this task runs an intervention on:
- **All 11 genuine-disagreement buildings** (not a sample — the full census found only 11, so
  the whole population is used, which exceeds the plan's 40-60 target being possible here; the
  cap does not bind).
- **A stratified negative-control draw, seed=42, up to 5 per zero-disagreement sub-bucket**
  (`GROUPMEDIAN_LEVELS_MED`-but-1 and `LEVELS_DEFAULT_LOW`) — these buildings get `levels=1`
  in **both** arms by construction, so baseline and treated should match to EnergyPlus float
  noise. This is the plan's "untreated hold-out subset reproduces the baseline" control, run
  for real rather than assumed.

## 3. Pre-registered prediction — written before any EnergyPlus run in this task

**Mechanism reasoned from code before seeing a result.** `footprint.py`'s own
`compute_form_factor()`: `envelope_surface_m2 = perimeter*num_floors*floor_to_floor_m +
2*footprint_area_m2`, `floor_area_m2 = footprint_area_m2*num_floors`. As `num_floors` rises
from 1, the `2*footprint_area_m2` term (roof + ground floor, fixed) is amortised over more
floor area, so the envelope-loss-per-floor-area (form factor) **falls** monotonically with
`num_floors`, most steeply between 1 and ~10 floors. Internal loads (lighting/equipment/people)
are per-floor-area constants in the archetype tables and do not change between arms. Everything
else (constructions, WWR, HVAC, schedules) is untouched between arms.

**Prediction, stated before running:**
1. **Sign: treated EUI < baseline EUI for all 11 genuine-disagreement buildings** (envelope
   loss per unit floor area falls as the single inflated floor is replaced by many thinner
   ones sharing the same roof+ground-floor envelope penalty).
2. **Magnitude scales with `recovered_levels`**: `austin_centre` (lev=45) shows the largest
   |Δ|%, `la_urban` (lev=7) and `nyc_urban` (lev=6) smaller and similar to each other.
3. **Mechanism test (X02's method): this is a per-storey effect, not a fixed per-building
   offset** — i.e. `CV(delta_eui / recovered_levels)` should be **lower** than `CV(delta_eui)`
   raw, the *opposite* conclusion from OPEN-56's zone-volume fix (which X02 showed was a fixed
   per-building artifact, not a per-zone physical effect). This one is a real envelope/geometry
   effect and is predicted to scale with the size of the geometry change.
4. **Negative controls**: `delta_eui ≈ 0` for the zero-disagreement buildings, within
   EnergyPlus's own run-to-run float noise (no formal threshold pre-registered; reported as
   observed).

**This prediction is reported below whether it holds or fails, per hard rule 8.**

## 4. A harness bug found and fixed mid-task, before any number was trusted

The first full run (build + simulate, all 21 buildings) produced two classes of failure beyond
the plan's known "empty output directory" pattern (hard rule 7):
- 4 directories genuinely empty (no `eplusout.err` at all) — the known pattern, fixed by
  hard rule 7's own remedy (serial re-verify): all 4 reproduced cleanly alone.
- 2 directories **not empty but wrong**: one had a real `** Severe **
  HVACTemplate:* objects found... must run ExpandObjects` fatal (looks like `-x` silently
  didn't apply); one had `Missing required property 'Building'`/`'GlobalGeometryRules'`
  (looks like a truncated IDF read). Both are outside hard rule 7's "empty directory" check
  and would have been scored as genuine failures.

Serially re-running both made them pass — consistent with a concurrency artifact, not a
defect in either arm's geometry. Investigating further (after the full 21-building run
completed) found something worse: two **"successful"** runs — `austin_centre/way_134807227`
(baseline, 1 floor, 3,917 m² footprint) and `austin_centre/way_516276237` (treated, 45
floors, 720 m² footprint) — reported **byte-identical `eplusout.sql`** (same 66,228,224-byte
file, same Total Building Area, same Total Site Energy) despite being two different buildings
with a >5x footprint difference and a 44-floor geometry difference. **One run silently
simulated the other's IDF and reported success.** This is a correctness failure, not an
availability failure, and it would not have been caught by any control this plan specifies.

**Root cause (best evidence, not EnergyPlus-source-confirmed):** all EnergyPlus invocations in
the first run shared one process working directory (`subprocess.run(...)` with no `cwd=`,
matching `open56_zone_volume_experiment.py`'s `run_ep()`, which this task's first draft
imported unchanged). EnergyPlus's `-x`/ExpandObjects preprocessing step appears to consult a
cwd-relative intermediate file rather than one scoped to `-d <outdir>`; two invocations from
the same cwd, run **231 seconds apart** (not a tight race), can still cross-contaminate.

**Fix:** every invocation now gets its own `cwd=str(outdir)` (`run_ep_isolated()` in
`scripts/analysis/open35_storey_intervention_2026-08-19.py`). The entire build+simulate phase
was re-run from scratch after the fix. Result: **zero empty/wrong-content failures on the
clean run** (all 42 EnergyPlus calls succeeded on the first pass, 0 severe/0 fatal
everywhere), plus an explicit post-hoc **contamination control** (added to the script) that
flags any two different `(cell, osm_id, arm)` rows sharing an identical
`(floor_area_m2, site_energy_gj)` pair. It flagged exactly one pair —
`austin_rural/way_1450169427` and `way_1450169428`, two negative-control buildings whose
footprints differ by 0.0005 m² (322.810477 vs 322.810944, evidently two near-duplicate
adjacent structures in OSM) — checked and confirmed a benign coincidence, not a repeat of the
bug (both are zero-effect negative controls either way).

**Consequence for anyone else running local EnergyPlus batches from this repo:**
`open56_zone_volume_experiment.py`'s `run_ep()` (and anything that imports it, as this task's
first draft did) carries this same latent risk when called more than once from a shared
process. **Recommended, not taken:** add `cwd=outdir` to that function directly, and add a
contamination control to any future batch-comparison script. Not fixed here because it is not
this task's file to change without a director ruling on shared analysis tooling.

## 5. Census control: no OSM cell had its `01_buildings.gpkg` re-fetched (hard rule 1/step 1)

Confirmed per building via `step1_fetch`'s own cache-hit log line for all 7 cells touched
(`nyc_suburban`, `nyc_rural`, `austin_rural`, `austin_suburban`, `nyc_urban`, `la_urban`,
`austin_centre`); `01_buildings.gpkg` was present and unchanged in every case (hard rule 11
re-verified live, not cited from a dated census).

## 6. Fidelity control — and a second bug it caught

**First attempt failed the control outright, and correctly, per hard rule 9.** The freshly
rebuilt baseline arm's EUI, computed by borrowing `open56_zone_volume_experiment.py`'s
"Total Site Energy / Total Building Area" read, was **systematically 15%–37% higher** than
the archived run-2 `total_eui_kwh_m2` for the identical 21 buildings (same IDF, confirmed
byte-identical by MD5 against the archived run-2 IDF for a spot-checked building). One-directional
across all 21 — not float noise. **This voided every number from the first attempt and none
was reported past this point**, per hard rule 9.

**Root cause:** `openubem/results/parser.py`'s production `total_eui_kwh_m2` (what every other
figure in this arc, including `open35_eui_consequence.csv`, is built from) is **not**
"Total Site Energy ÷ Total Building Area" from the ABUPS summary table — it is the **sum of
per-end-use EUIs from custom RunPeriod meters**, each divided by
`resolve_simulated_floor_area()`'s multiplier-aware `.eio` zone area (OPEN-01 ruling 6). The
ad hoc read borrowed from OPEN-56's script (built for a same-methodology A/B comparison, never
meant to be compared against archived production numbers) uses a different energy total and a
different area. The two are not interchangeable, and this had never been noticed before because
OPEN-56's task never compared against an archived figure.

**Fix:** re-parsed the same, already-completed `eplusout.sql`/`.eio` files with production's
own `openubem.results.parser.parse_building()` unchanged (`scripts/analysis/open35_storey_intervention_reparse.py`)
— no re-simulation needed, since the sql/eio outputs from the clean isolated-cwd run were
already correct; only the *reading* of them was wrong.

**Fidelity control, re-run: PASSED.** Max |diff| = **0.0047%**, mean |diff| = **0.0009%** across
all 21 buildings — float noise, as the plan's "untreated hold-out subset reproduces the
baseline" control requires. This is the number quoted from here on.

**Evidence:** `openubem/outputs/comparisons/open35_storey_intervention_results.csv` (first
attempt — ad hoc read, **superseded, do not cite the EUI columns in this file**, kept only for
provenance of the contamination-diagnosis narrative above);
`openubem/outputs/comparisons/open35_storey_intervention_results_v2.csv` (**authoritative** —
production `parse_building()`, fidelity-verified).

## 7. Results — the 11 genuine treatment buildings

| cell | osm_id | recovered levels | base EUI | treated EUI | Δ EUI | % change |
|---|---|---:|---:|---:|---:|---:|
| austin_centre | relation/7480583 | 45 | 74.58 | 104.82 | +30.24 | **+40.5%** |
| austin_centre | way/134807227 | 45 | 92.71 | 109.91 | +17.20 | **+18.6%** |
| austin_centre | way/516276237 | 45 | 104.78 | 109.56 | +4.78 | **+4.6%** |
| la_urban | way/1416444072 | 7 | 90.80 | 95.03 | +4.22 | **+4.7%** |
| la_urban | way/402234762 | 7 | 93.16 | 95.42 | +2.26 | **+2.4%** |
| la_urban | way/913603652 | 7 | 89.76 | 94.77 | +5.01 | **+5.6%** |
| nyc_urban | way/281344664 | 6 | 96.53 | 98.17 | +1.63 | +1.7% |
| nyc_urban | way/281345438 | 6 | 114.86 | 102.96 | -11.90 | **-10.4%** |
| nyc_urban | way/821626191 | 6 | 153.60 | 137.26 | -16.34 | **-10.6%** |
| nyc_urban | way/828447386 | 6 | 107.38 | 100.06 | -7.32 | **-6.8%** |
| nyc_urban | way/832347781 | 6 | 130.53 | 114.14 | -16.38 | **-12.6%** |

**Negative controls (10 buildings, `austin_rural` ×5 + `nyc_suburban` ×5): Δ EUI = 0.000000
exactly, for every one.** `levels` is 1 in both arms by construction, and the two independently
built and simulated IDFs (through the full production pipeline, not copied) produced
bit-identical EnergyPlus results. This is the strongest form of the plan's "untreated hold-out
subset reproduces the baseline" control, and it passed exactly.

## 8. Prediction scored against the outcome

1. **"Sign: treated < baseline for all 11" — REFUTED for the majority.** 7 / 11 positive
   (treated *higher*), 4 / 11 negative. The envelope-form-factor mechanism reasoned from
   `compute_form_factor()` is real in direction for `nyc_urban` (4 of 5 negative, matching
   the prediction) but is **overridden by something else** in `austin_centre` and `la_urban`
   (all 6 positive, several strongly so).
2. **"Magnitude scales with `recovered_levels`" — partially held.** `austin_centre` (lev=45)
   does show the largest |%| (up to +40.5%), well above `la_urban` (lev=7, ≤+5.6%) and
   `nyc_urban` (lev=6, ≤-12.6% magnitude). But `la_urban` (7) and `nyc_urban` (6) — nearly the
   same recovered level — differ mainly in **sign**, not magnitude ordering, so "scales with
   levels" is true only across the big gap to 45, not as a smooth gradient.
3. **"Per-storey effect, `CV(Δ/levels) < CV(Δ) raw`" — NOT RESOLVED, not confirmed or refuted.**
   Both CVs are dominated by a near-zero mean (the 7-positive/4-negative split), which makes
   the coefficient of variation itself unstable and uninformative here (raw CV ≈ 11.6,
   per-storey CV ≈ -2.7 — neither is the small, stable number X02 got for OPEN-56). **The
   honest read is that this mechanism does not reduce to a single per-building or per-storey
   number the way OPEN-56's did** — X02's test was built for a one-directional artifact and
   this effect is not one-directional.
4. **"Negative controls ≈ 0" — HELD exactly**, to the last digit EnergyPlus reports.

**A pattern the data suggests but 11 buildings across 3 cells cannot establish causally:** the
sign split lines up with climate zone, not archetype or footprint — `austin_centre` (ASHRAE 2A,
hot) and `la_urban` (3B, warm) are uniformly positive; `nyc_urban` (4A, mixed/cold) is mostly
negative. A cooling-dominated climate plausibly loses less from the single-inflated-floor's
worse form factor than it gains from something the taller treated geometry adds (more exterior
wall area exposed to solar/high outdoor temperature, or more zones each carrying their own
minimum ventilation); a heating-dominated climate plausibly behaves the other way, matching the
pre-registered envelope-loss mechanism. **Recorded as a lead, not a finding** — 3 cells is not
enough to separate climate from the two cells' other differences (archetype: `HighriseApartment`
vs `MidriseApartment`; the 45-storey case is also far outside the other two in magnitude).

## 8b. Imputation-tier compliance (hard rule 10)

The recovered value this task re-derives (`recovered_levels`, via `_impute_levels()`) uses that
function's own tier vocabulary — `OSM_OBSERVED` / `HEURISTIC_HEIGHT` / `GROUPMEDIAN_LEVELS_MED`
/ `LEVELS_DEFAULT_LOW` — which is separate from the fleet's general `HOTDECK_*`/`knn_fill`
imputation system (that system fills different columns; `levels`'s missing-both-inputs case is
handled entirely inside `_impute_levels`/`derive_num_floors`, never by `knn_fill`). The full
distribution across all 1,031 population buildings **is** printed and is the census in §1/§5 —
979+22 `LEVELS_DEFAULT_LOW`, 19+3 `GROUPMEDIAN_LEVELS_MED`-equal-to-1, 11 genuine
`GROUPMEDIAN_LEVELS_MED`-greater-than-1. Cross-check against `data_quality_flag` is inherited
from T07 in this same plan pass, which already confirmed (fleet-wide, zero disagreements) that
Stage-1's `no_floors`/`no_height` tokens agree with the `.isna()` predicates defining this exact
"neither" population, of which the 1,031 is a further, archetype-filtered subset; not re-derived
here to avoid duplicating that check.

## 9. Verdict

**The intervention ran with its control, and the control passed exactly** (10/10 negative
controls at Δ=0.000000; fidelity check 0.0009% mean error after the methodology fix). **The
census this task ran before spending any EnergyPlus compute is the more consequential result**:
the register's "archetype chosen at group-median storeys, geometry built at one" mechanism
numerically fires on only **11 of the 1,031 buildings (1.07%) that carry the categorical label**
— the other 98.9% get the same value (1) from both fallbacks, via different code paths, because
their cells have no ground-truth `levels` data to compute a real median from (or a real median
that happens to equal 1). **On the 11 where it does fire, the effect is real (0.0047% fidelity
error, exact-zero negative controls) but is not one-directional**: it costs 4 of them and
benefits 7, apparently along climate lines. **`157.1 kWh/m²` is not restated. No fleet
extrapolation is offered** — 11 buildings in 3 cells is a census of the genuine-disagreement
population, not a weighted sample of anything larger.

**Evidence:**
`scripts/analysis/open35_storey_intervention_2026-08-19.py` (census + build + isolated-cwd
simulate + contamination control),
`scripts/analysis/open35_storey_intervention_reparse.py` (production-methodology re-parse),
`openubem/outputs/comparisons/open35_storey_intervention_census.csv` (1,031 rows),
`openubem/outputs/comparisons/open35_storey_intervention_prep.csv` (21-building IDF-build
manifest with the floor-count control),
`openubem/outputs/comparisons/open35_storey_intervention_results_v2.csv` (authoritative
results).
