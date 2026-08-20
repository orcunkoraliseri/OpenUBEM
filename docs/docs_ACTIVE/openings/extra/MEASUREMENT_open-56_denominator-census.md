# MEASUREMENT — OPEN-56 / OPEN-01: does the Zone.Volume anomaly reach the EUI denominator?

**Task:** T03 of `docs/docs_ACTIVE/openings/implemenation/previous/PLAN_ten-items-2026-08-19.md`
**Date:** 2026-08-19
**Corpus:** `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet3/` (run 3), re-verified on disk at
start of task. Read-only. No production code touched.
**Script:** `scripts/analysis/open56_denominator_census_2026-08-19.py`
**Outputs:** `openubem/outputs/comparisons/open56_denominator_census_2026-08-19.csv` (6,804 rows,
per-building), `..._cellsummary_2026-08-19.csv` (reconciliation), `..._outliers_2026-08-19.csv`.

---

## Headline

**The ÷4.18 pattern does not reproduce anywhere else in the population this census can actually
check — and that population does not include the building class the anomaly came from.** The stop
condition (T03 §"How to test") is **not triggered**: zero of the checkable buildings sit near the
÷4.18 ratio. But the census's own coverage is 4% of the corpus, and the one cell holding the known
instance (`nyc_centre`) has **zero simulation output on disk** in run 3 — so this is a real negative
result on a narrow slice, not a fleet clearance.

---

## 1. Disk re-verification (binding instruction, done first)

Per cell, `.eio` count in `sim_out/` vs `.idf` count in `step3/idfs/`:

| cell | idf | sim_out (.eio) | status |
|---|---:|---:|---|
| austin_centre | 413 | 413 | present |
| austin_rural | 245 | 245 | present |
| austin_suburban | 437 | 437 | present |
| austin_urban | 425 | 425 | present |
| la_centre | 226 | 226 | present |
| la_rural | 149 | 149 | present |
| la_suburban | 1343 | 1343 | present |
| **la_urban** | 618 | **0** | **no sim_out at all — excluded** |
| **nyc_centre** | 738 | **0** | **no sim_out at all — excluded** |
| nyc_rural | 198 | 198 | present |
| nyc_suburban | 1589 | 1589 | present |
| nyc_urban | 1779 | 1779 | present |

**10 of 12 cells have run-3 simulation output on disk; `la_urban` and `nyc_centre` have none.**
`nyc_centre` is the cell that contains `relation_3566904`, the building the overnight pass's ÷4.18
finding came from — its own cell cannot be checked against other buildings in run 3.

The OPEN-56 A/B work directory that *did* produce the original finding survives separately, outside
`open48_refleet3`, at `%TEMP%/open56_fleet_cost/nyc_centre__relation_3566904/` (`base_out/`,
`treat_out/`, both complete with `.eio` and `.sql`). Used in §4 below.

---

## 2. Method

Simulated floor area: EnergyPlus's own multiplier-aware **Total Building Area**, computed the same
way `scripts/analysis/e02_t04_floor_area_audit.py` does it — `sum(Floor Area × Zone Multiplier ×
Zone List Multiplier)` over every zone flagged `Part of Total Building Area = Yes` in `eplusout.eio`.
This is the OPEN-01 remedy's own arithmetic, re-derived from the primary artifact, not read from a
downstream CSV.

Declared denominator: `footprint_area_m2 × levels`, read from each cell's `01_buildings.gpkg`, as the
plan's How step 2 specifies — **raw `levels`, not an imputed value.**

**Reconciliation control — passed, exactly, after one fix.** First pass mis-merged the two
`_partN`-suffixed stems in `nyc_urban` (`relation_17953040_part0/1`) back into one osm_id; checking
the source `.gpkg` showed these are **pre-split geometries already stored as two separate rows**, each
with its own `footprint_area_m2`. Fixed `stem_to_osm_id()` to stop stripping `_partN`. After the fix,
all 10 available cells reconcile exactly: `idf == sim_out dirs == gpkg rows`, zero drops, zero
`sim_not_in_gpkg`, zero `gpkg_not_in_sim`.

**Levels==1, no-multiplier control — passed.** 71 buildings fleet-wide have `levels = 1.0` and no zone
or zone-list multiplier; their ratio (sim / declared) has **median 1.0000, mean 1.0031, IQR
[0.9992 – 1.0005]**. The join is doing what it should. One of the 71 sits at ratio 1.18
(`la_centre/relation_2765901`) — see §3, same family as the four outliers.

---

## 3. Coverage — the load-bearing caveat

**Only 274 of 6,804 available-corpus buildings (4.03%) have a usable declared area.** The other 6,530
are dropped because `levels` is `NaN` in `01_buildings.gpkg` — this is exactly OPEN-35's population.
The census as specified (raw `levels`, no imputation) can only speak for buildings that already carry
a storey count; it says nothing about the buildings that don't, which is most of the fleet **and
includes `relation_3566904` itself** (`levels = NaN` there too — see §4).

Of the 274 checkable buildings:

- **Pooled ratio: median 1.0000, IQR [0.9997, 1.0000].**
- **4 / 274 (1.46%) fall outside ±10%**, all in `la_centre`, all ratio **1.12 – 1.18** (simulated area
  12–18% *larger* than declared, not smaller), all with `max_zone_multiplier = 1` — **no multiplier
  explanation.**
- **None of the 4 are near the 1/4.18 ≈ 0.239 ratio.** They are a smaller, opposite-direction, opposite-magnitude discrepancy from the OPEN-56 finding. Checked for an underground-zone or
  excluded-zone explanation (`underground` flag, `n_zones_excluded_not_in_total_area`) — both are
  zero/unset on all four. **Unexplained, and out of this task's scope to chase further**;
  flagged here as a distinct, smaller lead, not folded into OPEN-56.

| cell | osm_id | footprint_area_m2 | levels | ratio |
|---|---|---:|---:|---:|
| la_centre | relation/2765901 | 2,896.9 | 1 | 1.181 |
| la_centre | relation/6333146 | 3,669.3 | 14 | 1.158 |
| la_centre | relation/6366083 | 1,960.4 | 10 | 1.126 |
| la_centre | relation/6366084 | 1,730.6 | 10 | 1.119 |

**Stop condition check:** the plan's stop condition is triggered by "more than a handful of buildings
show the ÷4.18 pattern without a multiplier explanation." **Zero buildings show that pattern** among
the 274 checkable. **Not triggered.**

---

## 4. Targeted recheck — `nyc_centre / relation_3566904`, both arms

Read directly from the surviving OPEN-56 A/B work directory (independent of the run-3 corpus, since
`nyc_centre` has none):

| | baseline | treated |
|---|---:|---:|
| **eio-derived** (multiplier-aware, re-derived here) | 157,115.5 m² | 37,551.2 m² |
| **sql-reported** (EnergyPlus's own `Building Area` table) | 157,115.48 m² | 37,551.19 m² |
| cross-check, eio / sql | 1.000000 | 1.000001 |

**Exact reproduction of the overnight pass's figures** (157,115 → 37,551, ratio **4.1840**, matching
`157115/37551 = 4.1840` to 4 decimals), and the two independent extraction methods (raw `.eio`
parsing vs EnergyPlus's own SQL summary table) agree to six decimal places. **The original finding was
real and correctly measured — this is not an artifact of one extraction route.**

`relation_3566904` itself: `footprint_area_m2 = 2,496.09`, `levels = NaN`, `height_m = 46.6`. It is
**exactly the kind of building the main census cannot check** — no declared storey count, and its cell
has no run-3 simulation output at all. As a side calculation (not part of the specified census, offered
as context only): implied storeys = simulated area ÷ footprint. Baseline: 157,115.5 / 2,496.09 ≈ 63
storeys — physically absurd for a 46.6 m building. Treated: 37,551.2 / 2,496.09 ≈ 15 storeys — close to
`height_m / 3.5 ≈ 13.3`, the usual storey-height rule of thumb. **The treated (fixed) arm's area is the
physically plausible one; the baseline's is not.**

---

## 5. Verdict

**Does the anomaly reach the EUI denominator?** On the one building where it is known to occur, yes —
demonstrated twice now, by two independent extraction methods. **Is it unique fleet-wide?** **Not
answered by this census**, because the census's own join (raw `levels`, as specified) only covers 4%
of the corpus and structurally excludes the building class — and the specific cell — where the known
instance lives. Within the 4% it can check, the pattern does not recur; a different, smaller,
unexplained discrepancy (+12–18%, `la_centre`, 4 buildings) does, and is reported separately, not
folded in.

**Recommended, not taken:** re-run this census with an imputed storey count (the OPEN-35 fallback) so
the buildings most like `relation_3566904` are actually checkable, and/or get `nyc_centre` and
`la_urban` simulated in run 3 so the cell holding the known instance can be searched directly. Neither
is authorised by this task.

**OPEN-56's +0.98% / +0.84% fleet cost figure is unaffected by this measurement** — that statistic
already excluded `relation_3566904` for exactly this reason (overnight pass, X01 side-finding), and
nothing here changes the 69-building sample it was computed on.
