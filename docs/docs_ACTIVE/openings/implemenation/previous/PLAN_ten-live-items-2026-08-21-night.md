# PLAN — ten live items, second pass of 2026-08-21 (night)

- **Slug:** `ten-live-items-2026-08-21-night`
- **Date:** 2026-08-21 (night)
- **Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` — 16 live /
  46 retired / 62 total, next free `OPEN-63`.
- **Predecessor:** `implemenation/previous/PLAN_ten-live-items-2026-08-21.md` (T01–T10, CP-A–CP-D signed).
  Read its §9 director sign-off before starting: **two of its conclusions are corrected by this
  plan's §5.**
- **Why this pass exists.** The predecessor's tasks were built on the **E02 harvest**, which turned
  out to be meter-only everywhere and to carry an `.eio` in only 0.36 % of directories. The **adopted
  run** (`evidence/open48_refleet4/`) has **8,160 of 8,160 `.eio`, `.err` and `.end` files — 100 %
  coverage** — and nobody has read them. Every task below is a measurement that the harvest could not
  support and the adopted run can.

---

## 2. Hard rules for the executor

1. **Measure. Do not remediate.** No task here proposes, designs or applies a fix. If a remedy seems
   obvious, write one sentence naming it and stop. **The user rules; the director plans; you measure.**
2. **Never run compute on the Speed login node.** Nothing in this plan needs the cluster at all. If
   you think a task does, **STOP and say so** — do not `ssh`, do not `srun`.
3. **Do not invent a number.** If a column, file or signature named here does not exist, **STOP and
   quote the conflict**, naming the exact path you looked at and what you found instead. The
   predecessor's F5 was wrong and its executor was right to say so out loud — do the same.
4. **Never re-simulate.** Every input this plan needs is already on disk.
5. Use `.venv\Scripts\python.exe`. Bare `python` on this machine is a Windows Store stub and will
   fail silently in confusing ways.
6. **Scripts** go to `scripts/analysis/<item>_<slug>_2026-08-21b.py`. **CSVs** go to
   `openubem/outputs/comparisons/<item>_<slug>_2026-08-21b.csv`. **Docs** go to
   `docs/docs_ACTIVE/openings/extra/MEASUREMENT_<item>_<slug>.md`. No `.py` under `docs/`, ever.
7. **Do not commit.** Git is handled outside this session.
8. **Register every error you solve** in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, in the
   house format, before you close the task — and **search it first** before debugging anything.
9. **Append one progress-log entry per task to §8 of this file.** Other executors are writing to this
   same file concurrently: **re-read §8 immediately before appending**, and append after whatever is
   already there. Never rewrite another task's entry.
10. **Cap your own output.** Print summary numbers, never whole tables or file contents. Use
    `head -30`, `--stat`, `grep -c`. A single unbounded dump can cost more than the whole task.
11. **Denominators are mandatory.** Every rate you report names its numerator and denominator
    explicitly. "26 %" without "of what" is not a result.

---

## 3. File layout

**Read (never write):**

- `evidence/open48_refleet4/<cell>/results/05_results.csv` — the adopted per-building results.
- `evidence/open48_refleet4/<cell>/sim_out/<stem>/eplusout.eio` — **8,160, 100 % coverage.**
- `evidence/open48_refleet4/<cell>/sim_out/<stem>/eplusout.err` — **8,160, 100 % coverage.**
- `evidence/open48_refleet4/<cell>/fleet_staging/idfs/*.idf` — **8,160.**
- `evidence/open48_refleet4/<cell>/01_buildings.gpkg` — inputs, provenance columns.
- `openubem/outputs/comparisons/open35_fallback_population_2026-08-21.csv` — the 39.
- `openubem/outputs/comparisons/open53_meter_only_eui_2026-08-21.csv` — 8,153 rows, meter vs published.
- `openubem/outputs/comparisons/open03_storey_census_zfix.csv` — the storey census, 8,160 rows.

**Write:** only the three patterns in rule 6, plus §8 of this file.

---

## 4. Pinned dependency decisions

- **The corpus for this pass is `evidence/open48_refleet4/`, the adopted run — NOT
  `%TEMP%\ubem_e02_harvest`.** The harvest is meter-only in all 39,926 readable `.sql` and has `.eio`
  in 145 of 40,800 directories. **Do not read the harvest for anything in this plan.**
- **12 cells:** `{austin,la,nyc}_{centre,rural,suburban,urban}`.
- **Population:** 8,160 rows; **8,153 `simulation_status == "success"`**; the pooled headline is taken
  over the 8,153.
- **Pooled EUI is always Σ energy ÷ Σ area** (OPEN-43) — `Σ(eui × area) / Σ(area)`. **Never** the mean
  of per-building EUIs. Never merge per-cell results by averaging cell numbers.
- **Stem ↔ `osm_id` normalisation:** directory stems use `_` where `osm_id` uses `/`
  (`relation_17949119` ↔ `relation/17949119`). IDF/zone names additionally carry a
  `_F<n>_<STRATEGY>` suffix (`RELATION/17949119_F0_WHOLE`) — **strip the suffix to recover the
  building**, and note that one building has many zones. Some stems carry `_part0`/`_part1`; treat
  each part as its own simulation directory but **map both to the same `osm_id`** and say in your
  doc how many buildings had parts.
- **`.eio` `Zone Information` field order is fixed and given in F3.** Parse by position against the
  `! <Zone Information>` header line in the same file — **do not hardcode indices without checking
  that header is present in the file you are reading.**
- **Adopted fleet figure: 153.8231 kWh/m² pooled over 8,153.** It is **not** to be restated by any
  task here. T01 investigates why it does not reproduce exactly; that is not permission to change it.

---

## 5. Facts, with citations

- **F1 — the adopted run has full diagnostic coverage.** Director-counted 2026-08-21:
  `find evidence/open48_refleet4/*/sim_out -name "eplusout.eio" | wc -l` → **8,160**; same for `.err`
  and `.end`; **8,160** `sim_out` directories; **8,160** staged IDFs. This is the fact the whole pass
  rests on.
- **F2 — 🔴 the predecessor's F5 was WRONG and is corrected here.** It claimed `.eio` survives fatal
  runs, generalising from one building, and its T07 found only **145 of 40,800 (0.36 %)** harvest
  directories have one. **The error was looking in the harvest.** The adopted run is at 100 %. Where
  the predecessor's `MEASUREMENT_open-38-56_fatal-zone-volumes.md` reports coverage of 23/44 fatals
  and 47/200 controls, **this plan supersedes it on the adopted run** — the harvest findings are not
  fleet-scale and must not be quoted as such.
- **F3 — `.eio` `Zone Information` layout**, read from the header line present in every file:
  `Zone Name, North Axis, Origin X, Origin Y, Origin Z, Centroid X, Centroid Y, Centroid Z, Type,
  Zone Multiplier, Zone List Multiplier, Min X, Max X, Min Y, Max Y, Min Z, Max Z, Ceiling Height,
  Volume, Inside Conv Alg, Outside Conv Alg, Floor Area, Ext Gross Wall Area, Ext Net Wall Area,
  Ext Window Area, N Surfaces, N SubSurfaces, N Shading SubSurfaces, Part of Total Building Area.`
- **F4 — 🔴 the OPEN-56 volume stub is directly visible and is a literal 10.** Director-read
  2026-08-21, `nyc_urban/sim_out/relation_17949119/eplusout.eio`, zone `RELATION/17949119_F0_WHOLE`:
  **Ceiling Height 3.50, Floor Area 2343.46, Volume 10.00** — where floor area × ceiling height is
  **8,202 m³**. The stub is not an estimate to be inferred; it is a constant to be counted.
- **F5 — `05_results.csv` columns** (verified): `osm_id, footprint_area_m2, levels, height_m,
  archetype_id, zoning_strategy, data_quality_flag, heating_eui_kwh_m2, cooling_eui_kwh_m2,
  lighting_eui_kwh_m2, equipment_eui_kwh_m2, fans_eui_kwh_m2, pumps_eui_kwh_m2, dhw_gas_eui_kwh_m2,
  dhw_elec_eui_kwh_m2, dhw_eui_kwh_m2, cooking_eui_kwh_m2, refrigeration_eui_kwh_m2,
  elevators_eui_kwh_m2, total_eui_kwh_m2, gwp_*, iod, simulation_status, error_summary,
  floor_area_m2, floor_area_provenance, centroid_lon, centroid_lat`.
- **F6 — the fleet denominator is 24,333,586.4 m²**, director-verified as the sum of `floor_area_m2`
  over all 8,160 rows (identical over the 8,153 successes; the 7 failures carry zero area).
- **F7 — 🔴 the adopted headline does not reproduce exactly.** Two independent recomputations of
  `Σ(total_eui × floor_area)/Σ(floor_area)` over the 8,153 — one by the predecessor's T09, one by the
  director at CP-A — both return **153.8304**, not the adopted **153.8231**. Gap 0.0073 kWh/m²
  (0.005 %); some cells off by up to 0.18. **Unexplained. T01 owns this.**
- **F8 — the elevator adder explains most of the meter-vs-published gap.**
  `published_eui − meter_only_eui == elevators_eui_kwh_m2` to 1e-6 for **3,823 of 8,153**; pooled
  elevators **2.2421** against a pooled gap of **2.5539**. Residual pooled **0.31 kWh/m² (≈0.2 %)**,
  median 0, tail min **−502.68** / max **+873.37**. *(director addendum in
  `extra/MEASUREMENT_open-53_meter-only-eui-cost.md`)*
- **F9 — OPEN-35's undecided branch is 39 buildings**, token `GROUPMEDIAN_LEVELS_MED` in
  `archetype_source`; 38 simulated; reverting to `return 1` moves the denominator **−3.21 %**; the
  **top 5 carry ~71 %** of that and `relation/7480583` (`austin_centre`, 45 storeys assigned,
  published area **301,996.35 m²**) alone is **1.24 % of the fleet floor area**.
  *(`extra/MEASUREMENT_open-35_fallback-population.md` + director re-derivation)*
- **F10 — OPEN-62's readers all disagree with `auto_storey_count`:** corrected **29.07 %**, naive
  **39.78 %**, floor-surface **23.75 %**; the attic-excluded variant is unbuildable because
  `auto_attic_zone_count` is 0 for all 8,160.
  *(`extra/MEASUREMENT_open-62_storey-definition-table.md`)*
- **F11 — OPEN-17's seven targets, needs-a-value:** `levels` 7,719 (94.6 %), `function_tag` 7,741
  (94.9 %), `year_built` 5,913 (72.5 %, the only one filled), `postcode` 4,183, `building_tag` 4,105,
  `height_m` 2,806 (34.4 %), `geometry` 0. **`function_tag` and `building_tag` are never raw-null** —
  they carry placeholders. *(`extra/MEASUREMENT_open-17_target-null-census.md`)*
- **F12 — OPEN-14's nulls are concentrated:** 2,806/8,160 null `height_m`; `austin_rural`,
  `nyc_rural`, `nyc_suburban` are 100 % null and hold 72.4 %; `nyc_centre`'s measured fusion fill is
  **106/121 = 87.6 %**. *(`extra/MEASUREMENT_open-14_null-height-by-cell.md`)*
- **F13 — OPEN-19 at fleet scale:** pooled Austin **161.00**, LA **128.13**, NYC **165.27**; LA is the
  lowest, and archetype-matching keeps the sign. The historic **+38.8 %** is sim-vs-measured within
  LA and is a **different comparison** — do not conflate.
  *(`extra/MEASUREMENT_open-19_city-offset-fleet-scale.md`)*

---

## 6. Tasks

### T01 — the 153.8231 that will not reproduce

**What.** Find why two independent recomputations return 153.8304 and the adopted record says
153.8231, or prove the difference is not recoverable from what is on disk.

**Why.** F7. A headline that is "very nearly reproducible" is not reproducible. This is small enough
to be immaterial and important enough that it must not be rounded past silently.

**How.** Recompute pooled EUI over `evidence/open48_refleet4` under **each** of these row sets and
report all of them side by side: (a) all 8,160; (b) the 8,153 successes; (c) successes with
`floor_area_m2 > 0`; (d) successes with `total_eui_kwh_m2` non-null; (e) per-cell pooled, then
compared against the per-cell numbers in the fleet-restatement table the register cites for CP-2 of
2026-08-19 — locate that table by `grep -rn "153.82" docs/ | head -20` and cite the file:line you
used. Then test the two cheap hypotheses: **rounding** (does any subset round to 153.8231 at any
sensible precision?) and **a different source** (does an older `05_results.csv` under
`evidence/open48_refleet*` — there are five other run directories — reproduce 153.8231 exactly?).
Report which cells differ and by how much.

**How to test.**
- **C1** — your recomputation of row set (b) must return **153.8304 ± 0.0002**, reproducing F7. If it
  does not, stop: your join or your denominator is wrong, not the record.
- **C2** — state explicitly, as a headline sentence, whether **any** row set or run directory on disk
  reproduces **153.8231**. "No" is a complete and acceptable answer.

### T02 — OPEN-56: the volume stub, counted exactly, fleet-wide

**What.** Parse `Zone Information` from all **8,160** `.eio` and measure the volume defect exactly.

**Why.** F4. OPEN-56 has been carrying "roughly +1.0 kWh/m²" and "8,160/8,160 stub" as an estimate
and a flag. The `.eio` carries the actual number for every zone in the fleet and has never been read.

**How.** For every zone: `volume`, `floor_area`, `ceiling_height`, `zone_multiplier`, `min_z`,
`max_z`, and the building `osm_id`. Compute `expected_volume = floor_area × ceiling_height` and
`volume_ratio = volume / expected_volume`. Report: how many zones have **exactly 10.0**; the
distribution of `volume_ratio`; how many buildings have **every** zone stubbed vs **some**; total
fleet volume as-built vs as-expected. Write one row per zone to CSV, plus a per-building CSV.

**How to test.**
- **C3** — reproduce F4 exactly on `nyc_urban/relation_17949119`, zone `_F0_WHOLE`: ceiling height
  3.50, floor area 2343.46, volume 10.00. If your parser disagrees, your field offsets are wrong.
- **C4** — report the count of buildings with any stubbed zone against the register's claim of
  **8,160/8,160**. If it is not 8,160, **say so plainly and give the real number** — the register's
  figure came from a different check.
- **C5** — state the fleet total volume ratio (Σ as-built ÷ Σ expected) as a single number.

### T03 — OPEN-53: the residual that elevators do not explain

**What.** Size and characterise the ≈0.2 % pooled residual left after the elevator adder is removed.

**Why.** F8. The predecessor answered "what does meter-only cost" and the answer turned out to be
"mostly elevators". Nobody has looked at what is left, and it has a ±500–870 kWh/m² tail.

**How.** From `open53_meter_only_eui_2026-08-21.csv` joined to `05_results.csv`:
`resid = (published − meter_only) − elevators`. Report the residual's pooled value, its distribution,
and **how many buildings carry 50 % / 80 % / 90 % of the absolute residual**. Cross-tabulate the
outliers (`|resid| > 10 kWh/m²`) against `archetype_id`, `cell`, `zoning_strategy`,
`data_quality_flag`, `floor_area_provenance`, and the per-building zone count from T02's output if it
is available — **if T02 has not finished, proceed without it and say so.**

**How to test.**
- **C6** — reproduce F8's pooled elevator (2.2421) and pooled gap (2.5539) before computing anything
  new. Mismatch means a bad join.
- **C7** — report `n` and the pooled residual with its sign, and name the single largest contributor
  building by `|resid × area|`.

### T04 — OPEN-35: what was actually built for the 39

**What.** For each of the 39 fallback buildings, an evidence card of what the model **actually built**
versus what the fallback **assigned**.

**Why.** F9. This decision is now dominated by five buildings. The user cannot rule on
`relation/7480583` without knowing whether 45 storeys produced 45 storeys of zones.

**How.** For each of the 39 (from `open35_fallback_population_2026-08-21.csv`): from `.eio`, the zone
count, distinct `min_z`/`max_z` levels, total floor area summed over zones, max `max_z`; from
`05_results.csv`, `floor_area_m2`, `levels`, `height_m`, `archetype_id`, `simulation_status`,
`total_eui_kwh_m2`; from the population CSV, `current_num_floors` and `preopen35_num_floors`. One row
per building. **Sort by `current_floor_area_m2` descending and discuss the top 5 individually by
name** — that is the point of the task.

**How to test.**
- **C8** — 39 rows in, 39 rows out; the 38 simulated must be identifiable. State how many of the 39
  had a readable `.eio`.
- **C9** — for `relation/7480583`, report the built zone count and the number of distinct storey
  levels **as a headline number**, next to the 45 the fallback assigned. If they disagree, that is
  the finding — do not explain it away.

### T05 — OPEN-62: what each storey definition costs, in kWh/m²

**What.** Turn the storey-definition question from a disagreement table into a consequence table.

**Why.** F10. Four definitions disagree and none wins on agreement. The user cannot rule on an
abstract definition; they can rule on "this one moves the fleet number by X".

**How.** For each of the three buildable definitions in `open03_storey_census_zfix.csv`
(`layout_assign_storey_count`, `_naive`, `_floor`) plus `auto_storey_count` as the baseline: rebuild
the fleet floor-area denominator as `footprint_area_m2 × storeys` for every building, then recompute
the pooled EUI as `Σ(total_eui × published_area) ÷ Σ(redefined_area)` — i.e. **hold the per-building
energy fixed and vary only the denominator**, which is exactly what a definition change does without
re-simulation. Report, per definition: the fleet denominator, the pooled EUI, and the delta against
the adopted 153.8231. **State in one sentence, in the doc, that this is a denominator-only
sensitivity and not a re-simulated result.**

**How to test.**
- **C10** — reproduce F10's three agreement rates (29.07 / 39.78 / 23.75 %) before computing
  anything new.
- **C11** — the baseline definition must return a denominator within 1 % of F6's 24,333,586.4 m². If
  it does not, your `footprint × storeys` reconstruction disagrees with the published area — **report
  that as a finding**, it is interesting in itself, and continue with both numbers stated.

### T06 — the adopted run's own `.err` census, at 100 % coverage

**What.** Census all **8,160** `.err` files of the adopted run: fatals, severes, warnings, by class.

**Why.** F1 and F2. Every error statement this arc has made — OPEN-38's 86 % family, OPEN-09's 16
non-convergent, OPEN-45's marker defect — was measured on the harvest, a different corpus with five
geometry modes. **The adopted run's own error profile has never been counted.**

**How.** For each `.err`: the two-space `**  Fatal  **` marker (the one-space form is the OPEN-45
defect and finds nothing); count of `** Severe **`; count of `** Warning **`; the normalised class of
the **last** severe before a fatal, and of the first severe otherwise. Normalise by replacing numbers,
zone names and surface names with placeholders, exactly as the predecessor's
`MEASUREMENT_open-38_fatal-cause-census.md` §3 did. Report the top classes with counts and
denominators, and the count of buildings matching OPEN-09's real signature
`Inside surface heat balance did not converge` — **that exact string; `CheckWarmupConvergence`
matches nothing and an executor already refused a task over it.**

**How to test.**
- **C12** — total files read must be **8,160**. Any shortfall is a finding, not a rounding.
- **C13** — the OPEN-09 signature count must reproduce **16**. If it does not, report both your number
  and the 16 and do not adjust.

### T07 — OPEN-38 × OPEN-56: is volume degeneracy associated with failure, at full coverage?

**What.** The test the predecessor's T07 could only run on 23 of 44 harvest fatals, run properly on
the adopted run at 100 % coverage.

**Why.** F2. The harvest answer is not fleet-scale and should not be quoted. This corpus can settle it.

**How.** Join T02's per-building volume table to T06's per-building error table (both are outputs of
this plan — **if either is unfinished, wait for its CSV on disk rather than recomputing it**; if it
never appears, say so and stop). Compare the volume-degeneracy measures (fraction of zones stubbed,
volume ratio) between: (a) buildings with a fatal, (b) buildings matching the OPEN-09 non-convergence
signature, (c) everything else. Report rates with explicit denominators for each group. **If the stub
is universal — F4 suggests it may be — say so plainly: a constant cannot discriminate anything, and
that is a complete and useful answer that closes the question.**

**How to test.**
- **C14** — report |a|, |b|, |c| and confirm they partition the 8,160 (state any overlap between a
  and b explicitly rather than assigning arbitrarily).
- **C15** — if the stub rate is identical across groups, state in the doc's headline that **volume
  degeneracy cannot discriminate failure in this corpus**, and that this supersedes the harvest
  result.

### T08 — OPEN-17: does a source even exist for the six unwired targets?

**What.** For each of the six targets the imputation router does not fill, determine whether a source
column exists anywhere in the inputs on disk.

**Why.** F11. "Covers one of seven" is a statement about the router. It is not a statement about
whether the other six are fillable, and the user is being asked to decide about machinery without
knowing which targets have anything to feed them.

**How.** For each of `levels`, `function_tag`, `postcode`, `building_tag`, `height_m`, `geometry`:
list every column in `01_buildings.gpkg` across the 12 cells whose name or content plausibly carries
that target (report the column list per cell with `head -40`, not the data). For each, report how many
of the needs-a-value rows have a usable value in **some other column** of the same row. **Report
"no source exists" wherever that is the answer** — a negative result here is as decision-relevant as
a positive one.

**How to test.**
- **C16** — reproduce F11's seven counts from the gpkgs before doing anything else, including the
  placeholder-not-null behaviour of `function_tag` and `building_tag`. Quote the placeholder values
  you found.
- **C17** — one line per target stating source-exists yes/no and the count behind it.

### T09 — OPEN-14: is the 87.6 % extrapolation defensible?

**What.** Test whether `nyc_centre`'s null-height buildings resemble the other eleven cells', which is
the unstated assumption behind "≈2,352 would fill".

**Why.** F12. The extrapolation is labelled as one, but nobody has checked the population it
extrapolates from. Three cells are 100 % null, which is exactly the situation least like `nyc_centre`.

**How.** Compare the null-`height_m` populations of `nyc_centre` and each other cell on:
`footprint_area_m2` distribution (median, IQR), `archetype_id` mix, `levels` availability,
`data_quality_flag` mix, and urban/rural class. Report which cells are most and least like
`nyc_centre`, and **restate the ≈2,352 figure with a stated caveat, or give a defensible range** —
but **do not produce a new point estimate as if it were measured.**

**How to test.**
- **C18** — reproduce F12's 2,806 total and the three 100 %-null cells.
- **C19** — state, as a headline, whether the three 100 %-null cells are more or less like
  `nyc_centre` than the fleet average, since they carry 72.4 % of the gap.

### T10 — OPEN-19: is LA low because of its buildings or its climate?

**What.** Decompose the city-to-city EUI gap into archetype mix and per-archetype intensity.

**Why.** F13. "LA is lowest" is a result without a mechanism, and the item's whole question is whether
something climate-specific is missing from the model. A mix/intensity split says which.

**How.** Standard shift-share: pooled city EUI = Σ(share × intensity) over shared archetypes. Compute,
for LA vs Austin and LA vs NYC, how much of the gap is explained by **different archetype shares** and
how much by **different EUI within the same archetype**. Then report, for the three or four largest
archetypes by area, LA's heating and cooling EUI against the other cities' — **heating and cooling
separately**, because a climate story and a mix story leave different fingerprints there. Name the EPW
file used per cell from `02a_climate_epw.parquet` or the manifest, and report the heating/cooling
degree-day proxy if one is present; **if it is not present, say so and do not compute one.**

**How to test.**
- **C20** — reproduce F13's three pooled city numbers (161.00 / 128.13 / 165.27) before decomposing.
- **C21** — the mix and intensity components must sum to the total gap; state the residual of that
  identity.
- **C22** — state in one sentence whether the decomposition points at mix or at intensity, **without
  proposing a remedy** and without conflating this with the historic +38.8 %.

---

## 7. Stop-and-report points

- **CP-E — after T01, T02, T03.** The reproducibility question and the two OPEN-53/56 measurements.
- **CP-F — after T04, T05.** The two decision-support tables (OPEN-35, OPEN-62).
- **CP-G — after T06, T07.** The error census and the degeneracy test. **T07 depends on T02 and T06.**
- **CP-H — after T08, T09, T10.** Final.

At every checkpoint the **director** — not the executor — updates the register, the checklist, the
director prompt and the board. **The board is updated on every pass, without being asked**
(user directive, 2026-08-21).

---

## 8. Progress log

#### T01 — the 153.8231 that will not reproduce — completed 2026-08-21

**Artifacts:** `scripts/analysis/t01_headline-reproduction_2026-08-21b.py`,
`openubem/outputs/comparisons/t01_headline-reproduction_percell_2026-08-21b.csv`,
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_t01_headline-reproduction.md`.

**Result.** C1 reproduced: row set (b) (8,153 successes over `evidence/open48_refleet4`) pools to
**153.8304**, matching F7. Row sets (a)/(b)/(c)/(d) are all identical (153.8304, n=8,153,
area=24,333,586.4) because the 7 failures already carry zero floor area. Per-cell recompute is
within 0.02–0.18 kWh/m² of the restatement table at
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_fleet-restatement-2026-08-19.md:26-38` (located via
`grep -rn "153.82" docs/`). Rounding hypothesis rejected: 153.8304 at 0–5 dp never lands on 153.8231.
Different-source hypothesis tested and rejected two ways: (1) the restatement doc's own cited
provenance path, `%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet4\`, still exists on disk and
reproduces **153.8304 exactly** — identical to `evidence/open48_refleet4`, with an identical sorted
`osm_id` set; (2) the other five run directories under `evidence/open48_refleet*` are not candidates —
`open48_refleet` has all 12 cells but predates the `floor_area_m2` column (schema only has
`footprint_area_m2`), and `open48_refleet3`, `open48_refleet3_t02a3`, `open48_refleet3_t02a4` have
5, 0, and 1 of the 12 cells respectively.

**C2 headline: No.** Nothing on disk — including the record's own cited source directory —
reproduces 153.8231. The 0.0073 kWh/m² (0.005 %) gap is not recoverable from what is on disk. The
adopted 153.8231 figure is not restated or changed by this task.

**Deviations.** None from the plan's How. One addition beyond the plan's explicit "How": the TEMP
provenance path check, done because the restatement doc names it as the actual source of the
original 153.8231 computation and it is a legitimate "different source... on disk" test within T01's
own charge — not the `%TEMP%\ubem_e02_harvest` corpus §4 excludes (a different, meter-only harvest).

**Test status.** C1 passed (153.8304 ± 0.0002, exact match). C2 answered as required — a stated "no"
with the disk evidence behind it.

**Notes.** No error required registering in the debug-references file; the only runtime error
(`KeyError: 'floor_area_m2'` on `open48_refleet`'s older schema) was expected schema drift, handled
in-script by skipping with a stated reason, not a bug.

#### T03 — OPEN-53: the residual that elevators do not explain — completed 2026-08-21

**Artifacts:** `scripts/analysis/open53_residual-after-elevators_2026-08-21b.py`,
`openubem/outputs/comparisons/open53_residual-after-elevators_2026-08-21b.csv` (8,153 rows),
`openubem/outputs/comparisons/open53_residual-outliers_2026-08-21b.csv` (639 rows),
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-53_residual-after-elevators.md`.

**Result.** C6 reproduced F8 exactly: join of `open53_meter_only_eui_2026-08-21.csv` to
`05_results.csv` on `(cell, osm_id)` gave 8,153/8,153 matched, pooled elevators **2.2421**, pooled
gap **2.5539**, exact-match count **3,823 of 8,153** — all match F8. C7: pooled residual
**+0.3118 kWh/m²** (n=8,153), median 0, tail −502.68/+873.37, largest single contributor by
`|resid × area|` is `relation/7480583` (`austin_centre`, resid +100.75, area 301,996.4 m²) — the same
building F9 flags as 45-storey-assigned. Concentration: 9 buildings (0.11 %) carry 50 % of the
absolute residual mass, 26 (0.32 %) carry 80 %, 41 (0.50 %) carry 90 %. Outliers `|resid|>10`:
639 of 8,153 (7.84 %), strongly associated with `archetype_id == OpenUBEMUnknown` (613/650 Unknowns
are outliers, 94.3 %), `single_zone` zoning (496/3,238, 15.3 % vs 2–3 % for the other two strategies),
and the `VINTAGE_NAN_PERMISSIVE_DEFAULT` data-quality flags (up to 71.7 % outlier rate in one
category). `floor_area_provenance` is uninformative — all 8,153 rows are `eio_simulated`.
T02's per-building zone-count output was not available (T02 not run in this pass); the cross-tab
proceeded without it, per the plan's stated fallback.

**Deviations.** None.

**Test status.** C6 passed (exact match on all three F8 figures). C7 reported as required: n, signed
pooled residual, and named largest contributor.

**Notes.** No error required registering in the debug-references file.

#### T04 — OPEN-35: what was actually built for the 39 — completed 2026-08-21

**Artifacts:** `scripts/analysis/open35_evidence-cards_2026-08-21b.py`,
`openubem/outputs/comparisons/open35_evidence-cards_2026-08-21b.csv` (39 rows),
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-35_evidence-cards.md`.

**Result.** C8: 39 rows in, 39 rows out; 39/39 had a readable `.eio` (none of the 39 have a
`_part0`/`_part1` split — checked directly); 38/39 have `simulation_status == success`, matching
F9 exactly. The one non-simulated building is `way/266034056` (`nyc_centre`, `LargeHotel`). Top 5
by `current_floor_area_m2`, discussed individually by name: (1) `relation/7480583`
(`austin_centre`) — built 45 zones, 45 distinct storey levels, agreeing exactly with the 45 the
fallback assigned; published floor area 301,996.35 m² matches F9. (2) `way/134807227`
(`austin_centre`) — 45 built zones/levels vs 45 assigned, agrees. (3) `way/281344664`
(`nyc_urban`) — 6 built zones/levels vs 6 assigned, agrees. (4) `way/266034056` (`nyc_centre`) —
geometry built correctly (19 zones/19 levels vs 19 assigned) but never simulated. (5)
`way/231123149` (`austin_centre`) — 45 built zones but only 5 distinct storey levels (9
zones/floor, a zoning-strategy artifact, not a storey disagreement) vs 5 assigned storeys — storey
count agrees; `total_eui_kwh_m2` 377.30, a outlier flagged but not diagnosed (measurement only).

**C9 headline.** `relation/7480583`: built zone count 45, distinct storey levels 45, against the
45 the fallback assigned — **they agree.** Reported plainly per the plan's instruction not to
explain away a disagreement; here there is none to explain.

**Deviations.** None from the plan's How.

**Test status.** C8 passed (39/39 readable `.eio`, 38/39 simulated matching F9). C9 passed and
reported as a headline number next to the assigned 45.

**Notes.** No error required registering in the debug-references file.

#### T05 — OPEN-62: what each storey definition costs, in kWh/m² — completed 2026-08-21

**Artifacts:** `scripts/analysis/open62_denominator-sensitivity_2026-08-21b.py`,
`openubem/outputs/comparisons/open62_denominator-sensitivity_2026-08-21b.csv` (32,562 rows),
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-62_denominator-sensitivity.md`.

**This is a denominator-only sensitivity, not a re-simulated result** — stated explicitly in the
doc: per-building energy is held fixed at the adopted run's `total_eui_kwh_m2 × floor_area_m2`; only
the floor-area denominator is redefined as `footprint_area_m2 × storeys` per definition. No IDF was
rebuilt and no EnergyPlus run occurred.

**Result.** C10 reproduced F10's three agreement rates exactly (29.07 % / 39.78 % / 23.75 %) before
computing anything new. Per-definition, over the 8,153 successes: `auto_storey_count` (baseline)
denominator 24,320,581.9 m², pooled EUI **153.9127** (Δ +0.0896 vs adopted 153.8231);
`layout_assign_storey_count` denominator 12,634,619.6 m², pooled EUI **296.2690** (Δ +142.4459);
`layout_assign_storey_count_naive` denominator 8,464,264.2 m², pooled EUI **442.2412** (Δ
+288.4181); `layout_assign_storey_count_floor` denominator 15,841,047.7 m², pooled EUI **236.3004**
(Δ +82.4773). All three `layout_assign_*` definitions build a much smaller denominator (48–65 %
smaller) than the published area, because they assign fewer storeys than `auto_storey_count` for
most of the fleet — consistent with F10's low agreement rates — which inflates pooled EUI sharply
when energy is held fixed.

**C11.** Baseline (`auto_storey_count`) denominator **24,320,581.9 m²** vs F6's **24,333,586.4 m²**
— gap **−0.053 %**, inside the 1 % test; both numbers stated in the doc.

**Deviations.** None from the plan's How.

**Test status.** C10 passed (exact match on all three rates). C11 passed (−0.053 %, within 1 %).

**Notes.** No error required registering in the debug-references file.

#### T08 — OPEN-17: does a source even exist for the six unwired targets? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open17_t08_source_inventory_2026-08-21b.py`,
`openubem/outputs/comparisons/open17_t08_source_inventory_2026-08-21b.csv`,
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-17_t08_source-existence.md`.

**Result.** C16 reproduced all seven of F11's counts exactly from the gpkgs, including the
placeholder tokens (`OSM_MISSING` for `levels`/`postcode`/`height_m`/`function_tag`, `OSM_GENERIC`
for `building_tag`). Column inventory: 24 columns per gpkg (23 non-geometry + `geometry`), identical
across all 12 cells. Checked `surplus_tags` (per-row JSON of leftover OSM tags) plus one plausible
named alternate column (`roof_height_m` for `height_m`) as candidate sources.

**C17, one line per target:** `levels` — **no source exists**, 0 of 7,719 needs-value rows carry
`building:levels`/`levels`/`building:min_level` in `surplus_tags`, and no other column plausibly
carries it. `function_tag` — source exists but thin, 139 of 7,741 (1.80 %). `postcode` — source
exists but negligible, 1 of 4,183 (0.02 %). `building_tag` — source exists but negligible, 1 of
4,105 (0.02 %). `height_m` — source exists but thin, 25 of 2,806 (0.89 %); the named alternate
column `roof_height_m` is non-null for 0 of the 2,806. `geometry` — n/a, 0 of 8,160 need a value.

**Deviations.** `roof_shape` was considered as a candidate alternate column for `building_tag` and
explicitly rejected (it describes roof geometry, not building use — using it would have been an
invented association, not a measured source); this is recorded in the doc rather than silently
omitted.

**Test status.** C16 passed (exact match, 7/7). C17 reported, one line per target, in the doc and
above.

**Notes.** No error required registering in the debug-references file.

#### T09 — OPEN-14: is the 87.6 % extrapolation defensible? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open14_t09_extrapolation_check_2026-08-21b.py`,
`openubem/outputs/comparisons/open14_t09_null_height_population_compare_2026-08-21b.csv`,
`openubem/outputs/comparisons/open14_t09_distance_to_nyc_centre_2026-08-21b.csv`,
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-14_t09_extrapolation-check.md`.

**Result.** C18 reproduced F12's 2,806 fleet total and the three 100 %-null cells
(`austin_rural`, `nyc_rural`, `nyc_suburban`) exactly. Compared each cell's null-`height_m`
population (footprint-area distribution, `levels` availability, `data_quality_flag` `generic_tag`
rate, archetype-mix top-3 overlap) against `nyc_centre`'s, via a composite distance score (four
normalised components, reported alongside the score, not just the score alone).

**C19 headline.** Mean composite distance to `nyc_centre` for the three 100 %-null cells is
**0.839**, versus **0.723** across all eleven non-`nyc_centre` cells — **the three cells carrying
72.4 % of the gap are measurably less like `nyc_centre` than the fleet average, not more.**
`nyc_suburban` (56.6 % of the fleet's null-height total on its own) ranks 10th of 11, the most
dissimilar cell in the set: dominant archetype `MidriseApartment` (61.6 %) vs `nyc_centre`'s
`LargeOffice` (39.7 %), median footprint area 100.0 m² vs 1,384.5 m² (14× smaller), 0.0 % vs 11.6 %
`levels`-availability.

**Restatement (per plan instruction — no new point estimate).** The ≈2,352-of-2,685 extrapolated
fill figure is not replaced with a new number — no fusion-tier run against any other cell exists on
disk. It is restated with the caveat this task adds: it should be read as an **upper-bound-leaning**
extrapolation, not a central estimate, because its largest single contributor population
(`nyc_suburban`) is the most dissimilar to the population the 87.6 % rate was measured on. A
defensible numeric range was not constructed, because doing so would require running the fusion
tier against at least one of the dissimilar cells, which is outside this task's scope (same custody
block the source doc names) — stated explicitly in the doc rather than filled with an invented
range.

**Deviations.** None from the plan's How. The composite-distance metric is a similarity heuristic
built for this task only (documented as such), not a validated statistical test.

**Test status.** C18 passed (exact match). C19 passed and reported as the doc's headline sentence.

**Notes.** No error required registering in the debug-references file.

#### T02 — OPEN-56: the volume stub, counted exactly, fleet-wide — completed 2026-08-21

**Artifacts:** `scripts/analysis/open56_volume-stub-fleetwide_2026-08-21b.py`,
`openubem/outputs/comparisons/open56_volume-stub-zones_2026-08-21b.csv` (46,127 rows),
`openubem/outputs/comparisons/open56_volume-stub-buildings_2026-08-21b.csv` (8,159 rows),
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-56_volume-stub-fleetwide.md`.

**Result.** Parsed `Zone Information` by header position (index resolved dynamically from the
`! <Zone Information>` line, not hardcoded) across all 8,160 `.eio`, all of which carry the header.
**C3** reproduced F4 exactly on `nyc_urban/relation_17949119` `_F0_WHOLE`: ceiling height 3.50,
floor area 2343.46, volume 10.00. 46,127 zones parsed; **42,269/46,127 (91.64 %) have
`volume == 10.0` exactly.** Buildings grouped by `osm_id` with `_part0`/`_part1` merged to one
building (1 such pair, `relation/17953040`) → **8,159 distinct buildings** from 8,160 sim
directories. **C4:** buildings with *any* stubbed zone = **8,159/8,159 (100 %)**; buildings with
*all* zones stubbed = **7,769/8,159 (95.22 %)**, not the register's claimed 8,160/8,160 — the
register's figure describes "any stub" (universal), not "all zones stubbed" (which is not
universal); reported plainly, no correction made. **C5:** fleet volume ratio (Σ built ÷ Σ expected)
= **0.133921** (Σ built 11,477,577.85 m³, Σ expected 85,704,214.36 m³). Per-zone `volume_ratio`
distribution: min 0.0000, p25 0.0108, median 0.0245, p75 0.0633, max 5.4945.

**Deviations.** None from the plan's How. Building-level grouping uses the plan's stated
part-merging rule (§4); this yields 8,159 buildings, one fewer than the 8,160-row population,
stated explicitly rather than silently reconciled.

**Test status.** C3 passed exactly. C4 and C5 computed and reported as required; the register's
8,160/8,160 claim does not reproduce under the "all zones stubbed" reading and this is stated as
the finding.

**Notes.** No error required registering in the debug-references file. An off-by-one bug in the
first draft of the header-index parser (an artifact prefix-strip shifted indices by one, producing
zero parsed zones) was caught and fixed before any number was reported — not registered as a debug
entry since it never produced an output.

#### T06 — the adopted run's own `.err` census, at 100 % coverage — completed 2026-08-21

**Artifacts:** `scripts/analysis/open38-09-45_err-census-fleetwide_2026-08-21b.py`,
`openubem/outputs/comparisons/open38-09-45_err-census-buildings_2026-08-21b.csv` (8,160 rows),
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38-09-45_err-census-fleetwide.md`.

**Result.** **C12:** 8,160/8,160 `.err` files read, no shortfall. Two-space `**  Fatal  **` marker:
**7/8,160** files. `** Severe  **` (two-space) fleet-wide total: **110**. `** Warning **`
(one-space) fleet-wide total: **339,168**. All 7 fatals have an identifiable preceding severe
(0/7 `no_preceding_severe`). **C13:** OPEN-09 exact-string signature
(`Inside surface heat balance did not converge`) count = **16/8,160**, reproducing the register's
16 exactly. Severe-message classes, normalised (numbers/zone/surface placeholders), over the
26 files carrying >=1 severe: `DetermineShadowingCombinations…non-convex` 19/26, `Temperature (low)
out of bounds…` 6/26, `CalcHeatBalanceInsideSurf: The temperature of…` 1/26.

**Deviations.** None from the plan's How.

**Test status.** C12 passed (8,160/8,160). C13 passed (16 reproduced exactly).

**Notes.** No error required registering in the debug-references file.

#### T07 — OPEN-38 × OPEN-56: is volume degeneracy associated with failure, at full coverage? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open38-56_volume-degeneracy-vs-failure_2026-08-21b.py`,
`openubem/outputs/comparisons/open38-56_volume-degeneracy-vs-failure_2026-08-21b.csv` (8,160 rows),
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-38-56_volume-degeneracy-vs-failure.md`.

**Result.** Joined T02's per-zone volume table to T06's per-run error census on `(cell, stem)`
(the sim-run level both share natively; 8,160 rows). **C14:** (a) fatal = **7**, (b) OPEN-09
signature = **16**, (c) everything else = **8,143**; overlap(a,b) = **6**;
`7 + 16 + 8,143 − 6 = 8,160` — confirmed, partitions the corpus exactly. Volume-degeneracy
measures per group: (a) any-zone-stubbed 7/7 (100 %), all-zones-stubbed 7/7 (100 %), mean
frac_stub 1.000000; (b) any-zone-stubbed 16/16 (100 %), all-zones-stubbed 7/16 (43.75 %), mean
frac_stub 0.916714; (c) any-zone-stubbed 8,143/8,143 (100 %), all-zones-stubbed 7,762/8,143
(95.32 %), mean frac_stub 0.991732.

**C15 headline.** "Any zone stubbed" is **100 % in all three groups** — fatal, OPEN-09-signature,
and everything else. **A constant cannot discriminate anything: volume degeneracy cannot
discriminate failure in this corpus.** The "all zones stubbed" rate does vary (100 % / 43.75 % /
95.32 %) but does not track failure monotonically — group (b), the failing group, has the *lowest*
all-stubbed rate, below the non-failing group (c); at n=7 and n=16 this is not a usable signal
either way. This supersedes the predecessor's partial-coverage harvest result (23/44 fatals, 47/200
controls) per F2.

**Deviations.** None from the plan's How. Both dependency CSVs (T02, T06) were present on disk at
run time, so no wait was needed.

**Test status.** C14 passed (partition confirmed with stated overlap). C15 passed and reported as
the doc's headline sentence.

**Notes.** No error required registering in the debug-references file.

#### T10 — OPEN-19: is LA low because of its buildings or its climate? — completed 2026-08-21

**Artifacts:** `scripts/analysis/open19_t10_shift_share_2026-08-21b.py`,
`openubem/outputs/comparisons/open19_t10_shift_share_2026-08-21b.csv`,
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-19_t10_shift-share.md`.

**Result.** C20 reproduced F13's three pooled city numbers exactly from `05_results.csv`
(austin 161.00 n=1,520; la 128.13 n=2,330; nyc 165.27 n=4,303) before decomposing anything.
Shift-share run on the existing 15-archetype matched set (`open19_city_offset_2026-08-21.csv`,
`level == archetype_matched`), whose share-weighted reconstruction independently reproduces F13
§3's matched-subset numbers exactly (154.94 / 129.09 / 172.77).

**C21.** LA vs Austin (matched basis): gap −25.8507, mix effect −7.3716 (28.5 %), intensity effect
−18.4792 (71.5 %), mix + intensity = gap exactly, **residual −0.000000** (exact by construction,
stated explicitly). LA vs NYC: gap −43.6760, mix effect −6.6899 (15.3 %), intensity effect −36.9861
(84.7 %), residual **−0.000000**.

**Top 4 archetypes by combined matched-set floor area** (LargeOffice, TallBuilding,
MidriseApartment, MediumOffice), heating/cooling reported separately per city: in all four, LA's
heating **and** cooling are both lower than Austin's in the same direction — not the fingerprint a
climate-only story would leave (a colder/hotter climate should push heating and cooling in opposite
directions, not both down together).

**C22 headline.** The decomposition points at **intensity**, not mix — 71.5 % (LA vs Austin) and
84.7 % (LA vs NYC) of the gap is within-archetype, same-building-type intensity difference, not
different archetype shares. No remedy proposed. Explicitly **not** conflated with the historic
+38.8 % sim-vs-measured figure, which this task does not touch (stated in the doc's §0 scope note).

**EPW/degree-day.** One EPW file per cell named exactly (all 12 confirmed unique-and-singular).
`02a_climate_epw.parquet` carries no heating/cooling degree-day proxy column
(`osm_id, climate_zone, climate_zone_method, county_geoid, state, epw_path,
provenance_climate_zone`) — none was computed, per the plan's instruction.

**Deviations.** None from the plan's How.

**Test status.** C20 passed (exact). C21 passed, residual stated as exactly 0 (floating-point) for
both comparisons. C22 reported as the doc's headline sentence, no remedy, no conflation.

**Notes.** No error required registering in the debug-references file.

---

## 9. Director sign-off — 2026-08-21 (night pass)

Ten tasks, four concurrent Sonnet executors, ten progress entries appended to §8 with **zero
collisions** (each re-read the file first, as rule 9 required). Audit per CLAUDE.md: progress entries
present → every control C1–C22 checked → file set compared against §3 → citations checked for each
unplanned decision. **Only the planned files were touched** — 10 scripts under `scripts/analysis/`,
13 CSVs under `openubem/outputs/comparisons/`, 10 `MEASUREMENT_*.md` under `openings/extra/`, and §8
of this doc. Nothing was committed. Every load-bearing number below was re-derived by the director
directly, not by a checking agent.

**CP-E — T01, T02, T03. SIGNED, with a director extension to T02.**

C1–C7 all reported and reproduced. T01 answered C2 as a **stated negative**: nothing on disk returns
153.8231, including `%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet4\` — the path the restatement
doc itself names as the source of the original computation. That check was beyond the plan's literal
"How"; it is **accepted and adopted**, because it converts the loose end from "unexplained" into
"not recoverable from the record's own cited source". The five other `evidence/open48_refleet*` dirs
are correctly excluded on schema and coverage grounds.

T02 reproduced independently by the director from
`open56_volume-stub-zones_2026-08-21b.csv`: **42,269 of 46,127 zones (91.64 %)** carry
`Volume == 10.0` exactly; **8,159 of 8,159 buildings (100 %)** have at least one; **7,769 (95.22 %)**
have every zone stubbed; fleet ratio **0.133921** (11,477,578 m³ built against 85,704,214 m³
expected). All four figures match the executor to the digit.

**Director extension — the stub is deterministic by zone role, which the executor did not report.**
Cross-tabulating `is_stub` against the zone-name suffix:

| Zone role | Zones | Stubbed |
|---|---|---|
| `WHOLE` | 22,562 | **100.00 %** |
| `PERIM*` | 20,581 | 95.75 % |
| `CORE` | 2,984 | **0.00 %** |

and **all 3,858 non-stubbed zones fall within 1 % of `floor_area × ceiling_height`** (min ratio
0.9988, max 1.0029). The volume writer is therefore *correct whenever it fires* — it simply never
fires for a `WHOLE` zone and almost never for a perimeter zone. OPEN-56 is a single code path, not a
data-quality spread. **This is a measurement, not a remedy** (rule 1); no fix is proposed here.

T03's arithmetic checks: pooled gap 2.5539 − pooled elevators 2.2421 = **+0.3118**, and
0.3118 / 153.83 = **0.203 %**, consistent with the "0.2 %" headline. The concentration result
(9 buildings carrying 50 % of absolute residual mass, 41 carrying 90 %) is the operative finding —
**OPEN-53's residual cannot be closed by a flat fleet-wide adjustment.** The executor correctly
recorded that `floor_area_provenance` was uninformative (constant) rather than dropping it silently.

**CP-F — T04, T05. SIGNED. T04 closes a loose end left open at CP-B of the previous plan.**

C8–C11 reported. **T04 settles the `relation/7480583` basis conflict that CP-B could only rule on by
argument.** CP-B recorded two irreconcilable areas for that building — published 301,996.35 m² against
a script-recomputed 242,204.26 m². The `.eio` now answers it from what was actually built: **45 zones
across 45 distinct storey levels, summing to 301,996.35 m², max Z 157.5 m.** The published figure is
the simulated one; the recomputed `footprint × storeys` basis was wrong. **CP-B's −3.21 % stands, and
now rests on measurement rather than on inference.** C9 found no discrepancy: the fallback assigned 45
and the model built 45.

T05 re-derived independently by the director from `open62_denominator-sensitivity_2026-08-21b.csv`,
holding energy fixed at `eui × published_area` and varying only the denominator:

| Definition | Denominator (m²) | Pooled EUI |
|---|---|---|
| `auto_storey_count` (baseline) | 24,320,581.9 | 153.91 |
| `layout_assign_storey_count` | 12,634,619.6 | 296.27 |
| `layout_assign_storey_count_floor` | 15,841,047.7 | 236.30 |
| `layout_assign_storey_count_naive` | 8,464,264.2 | **442.24** |

C11 passes — the baseline denominator is within **−0.053 %** of the pinned 24,333,586.4 m². All four
pooled figures reproduce the executor exactly. **This is the largest lever on the headline found in
either pass:** the three alternative definitions roughly halve the denominator and swing the headline
from 154 to as much as 442 kWh/m² — a factor of ~2.9 — **with no re-simulation whatsoever**. OPEN-62
had been carried as a bookkeeping detail; it is not one. The executor made no recommendation, as
rule 1 required.

**CP-G — T06, T07. SIGNED. T07 supersedes the under-covered predecessor result and retires the F5
caution.**

C12–C15 reported. C12: **8,160 of 8,160 `.err` read, no shortfall** — the 100 % coverage claimed in
F1 held under execution. C13 reproduces the register exactly: the OPEN-09 signature
`Inside surface heat balance did not converge` appears in **16 of 8,160**. Fatals (two-space marker)
**7**; severes 110.

C15 is a **clean negative and is accepted as a complete answer**: "any zone stubbed" is **100 % in all
three groups** (7 fatal / 16 non-converging / 8,143 remainder), and a constant discriminates nothing.
This **supersedes the previous plan's 23-of-44 partial-coverage result**, which was reachable only
because that plan's F5 was wrong. The ⚠️ caution issued at CP-C of `PLAN_ten-live-items-2026-08-21.md`
— "OPEN-38's volume test is under-covered" — is hereby **discharged**: the test has been redone at
full coverage and the answer is that volume degeneracy has no discriminating power here.

**CP-H — T08, T09, T10. SIGNED, with one decomposition basis clarified.**

C16–C22 reported. T08's headline is the useful negative the plan invited: **`levels` has no source
anywhere in the corpus** — 0 of 7,719 needs-value rows carry any levels-related OSM tag in
`surplus_tags` — and it is simultaneously the largest hole (94.6 % of the fleet). No amount of wiring
fixes OPEN-17's biggest gap; that requires a new data source. The other four targets trickle at
0.02–1.80 %.

T09 correctly **refused to produce a new point estimate** and instead qualified the existing one: the
three 100 %-null cells carrying 72.4 % of the gap are *less* similar to `nyc_centre` than the fleet
average (0.839 vs 0.723), and `nyc_suburban` — 56.6 % of the null-height total on its own — is the
most dissimilar cell of all eleven. The ≈2,352 figure therefore **leans upper-bound** and is not
replaced. This is the right call under rule 2.

⚠️ **T10 — the mix/intensity split depends on a convention the entry does not name.** The director
re-derived the decomposition. The **gaps reproduce exactly** (LA−Austin **−25.85**, LA−NYC **−43.68**)
and the identity closes to floating-point in both cases. But the three-term decomposition is:

| Comparison | Gap | Mix | Intensity | Interaction |
|---|---|---|---|---|
| LA vs Austin | −25.85 | −7.37 | −11.12 | **−7.36** |
| LA vs NYC | −43.68 | −6.69 | −22.69 | **−14.29** |

The executor's reported 28.5 / 71.5 and 15.3 / 84.7 splits are recovered exactly **only by folding the
interaction term into intensity**. That is a legitimate convention, but the interaction term is large
— 28 % of the Austin gap and 33 % of the NYC gap — so **the split is convention-dependent and must be
quoted with its basis.** Held out separately, mix carries **39.9 %** of the LA-vs-Austin gap, not
28.5 %. **The direction survives either way** — intensity outweighs mix in both comparisons under both
conventions — so T10's headline stands, but "driven by intensity, not mix" overstates the
LA-vs-Austin case, where mix carries roughly 40 %.

Two further notes on T10, both in the executor's favour: the shift-share matrix is the **matched
15-archetype subset**, whose pooled city figures (Austin 154.94, LA 129.09, NYC 172.77) differ from
F13's full-population 161.00 / 128.13 / 165.27 — the restriction is legitimate and **LA remains lowest
under both**, so the conclusion is robust to it. And the refusal to conflate this sim-vs-sim result
with the historic sim-vs-measured **+38.8 %** was again explicit, as C22 required.

**Outcome of the pass: no item closed, no item opened, no published number moved, no ruling taken.**
Ten items now hold a measurement they lacked. Three results change the register's picture materially:
OPEN-56 is fleet-wide and mechanistically localised, OPEN-62 is a ~2.9× lever rather than a detail,
and OPEN-17's largest hole has no available source. One previous caution is **discharged** (F5 /
OPEN-38 coverage) and one previous ruling is **confirmed by measurement** (CP-B's −3.21 %). Two new
basis caveats are recorded rather than smoothed: T10's interaction term, and T01's now-definite
negative on the headline's reproducibility.
