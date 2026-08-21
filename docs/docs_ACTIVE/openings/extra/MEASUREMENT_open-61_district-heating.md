# MEASUREMENT — OPEN-61: District Heating mechanism and size on 48 `layout_assign` samples

**T01 of `PLAN_five-items-2026-08-20-late.md`.** Executor session, 2026-08-20. Local only, no
sbatch/ssh. Harness: `scripts/analysis/open61_district_source_2026-08-20.py`. Output:
`openubem/outputs/comparisons/open61_district_source.csv` (48 rows, one per sample building).

## Pre-registered controls (written before any of C1–C3 were run)

- **C1** — on `way_1008727470`, the reader must reproduce **0.72 GJ** District Heating at both
  the `Water Systems` row and the `Total End Uses` row of the ABUPS `End Uses` table.
  Expectation: pass, since this is a direct re-read of fact D4.
- **C2** — for every one of the 48 buildings, for every fuel column, the sum of the individual
  end-use rows must equal that column's `Total End Uses` row to within 0.5%. Expectation: pass
  for (nearly) all 48 — this is EnergyPlus's own arithmetic, not a measurement of the phenomenon.
  Any failure would mean the table itself is inconsistent, which was not expected.
- **C3** — count of the 48 whose District Heating `Total End Uses` is exactly 0.00 GJ.
  Expectation, going in: unknown — this is the number the task exists to produce. The plan's own
  stop condition: if all 48 are zero, D4's building is anomalous and T02 does not proceed.

## Mechanism (part a) — CONFIRMED

**Hypothesis:** a `WaterUse:Equipment`/`WaterUse:Connections` pair not served by a plant loop has
its energy booked by EnergyPlus to the `District Heating` column because there is no modelled
plant to charge it to.

Single-building test, `way_1008727470` (austin_centre): copied
`scratchpad/open03-untrimmed-sample/austin_centre/step3_layout_assign/idfs/way_1008727470.idf`
into scratch (`scratchpad/open61_c2_experiment/{baseline,treated}/`), and in the **treated** copy
deleted only the two orphan objects `WATERUSE:EQUIPMENT` (`DHW_WaterUse_OpenUBEMUnknown`) and
`WATERUSE:CONNECTIONS` (`DHW_WaterConn_OpenUBEMUnknown`) — 24 lines, no other edit. Both arms run
with `run_ep_isolated()` (`scripts/analysis/open35_storey_intervention_2026-08-19.py:95`), each in
its own working directory, same EPW
(`USA_TX_Austin-Camp.Mabry.ANGB.722544_TMYx.2011-2025.epw`).

| | baseline (`scratchpad/open61_c2_experiment/baseline/out/eplusout.sql`) | treated (`.../treated/out/eplusout.sql`) |
|---|---|---|
| Water Systems, District Heating | 0.72 GJ | **0.00 GJ** |
| Total End Uses, District Heating | 0.72 GJ | **0.00 GJ** |
| Water Systems, Natural Gas | 11.68 GJ | 11.68 GJ (unchanged) |
| Total End Uses, Natural Gas | 16.48 GJ | 16.51 GJ |
| Total End Uses, Electricity | 42.02 GJ | 41.93 GJ |

Deleting the orphan pair drives District Heating from 0.72 GJ to exactly 0.00 GJ. **CONFIRMED.**

Mechanically, in the source IDF (`.../austin_centre/step3_layout_assign/idfs/way_1008727470.idf`,
lines 811–878): `WATERHEATER:MIXED` (`DHW_Heater_OpenUBEMUnknown`, fuel `NaturalGas`, efficiency
0.808) has its `Use Side Inlet Node Name` and `Use Side Outlet Node Name` fields **blank** — it
runs in EnergyPlus's stand-alone mode, using its own `Peak Use Flow Rate` /
`Use Flow Rate Fraction Schedule Name` fields directly, no plant needed. Separately,
`WATERUSE:CONNECTIONS` (`DHW_WaterConn_OpenUBEMUnknown`) also has blank `Inlet Node Name` /
`Outlet Node Name` fields, and is not on any `Branch`/`PlantLoop` (fact D6: zero `PlantLoop`
objects in this model). The two objects are two **entirely separate, unwired** hot-water demands
in the same model, both driven from the same schedules and the same peak flow rate value
(`9.468105e-07`). EnergyPlus computes the sensible/latent load needed to heat the
`WaterUse:Connections` stream from mains to its target temperature and, finding no plant supply
attached, books it to `District Heating` by default rather than dropping it or failing.

## Part (b) — additional, not double-counting, but evidence is limited to this one pair

Removing the orphan objects left `Water Systems, Natural Gas` **bit-identical** (11.68 → 11.68 GJ);
`Total End Uses, Natural Gas` moved by +0.03 GJ (16.48 → 16.51, floating-point/rounding scale, not
11.68's worth). If the district-heating energy were the same physical load double-booked under two
fuel columns, removing the orphan pair should have reduced the gas number by a comparable amount —
it did not. **The district-heating term is additional energy, not a duplicate of the gas water
heater's load**, for this building. This is a single-building test; it establishes the mechanism,
not a fleet-wide magnitude claim for part (b) — that is control C1/C3/the per-cell table below.

## C1, C2, C3 — outcomes

- **C1: PASS.** `way_1008727470` reproduced 0.72 GJ at both `Water Systems` and `Total End Uses`.
- **C2: PASS on all 48/48.** Every fuel column on every building summed its individual end-use
  rows to its `Total End Uses` row within 0.5% (script's `check_c2`, `c2_pass` column in the CSV).
  No building excluded.
- **C3: 43 of 48 have District Heating `Total End Uses` exactly 0.00 GJ.** 5 of 48 are non-zero.
  This is **not** 48 — the plan's stop condition ("if C3 shows all 48 at zero, the item changes
  shape and T01 stops") does not fire. CP-1 proceeds to director review.

## Per-cell district-heating share of Total End Uses (12 cells, n=4 each, no pooled number)

| Cell | n | n zero | Non-zero building(s) and their share of Total End Uses |
|---|---|---|---|
| austin_centre | 4 | 3 | `way_1008727470` = 1.216% |
| austin_rural | 4 | 4 | none |
| austin_suburban | 4 | 4 | none |
| austin_urban | 4 | 4 | none |
| la_centre | 4 | 3 | `way_425993511` = 1.766% |
| la_rural | 4 | 4 | none |
| la_suburban | 4 | 4 | none |
| la_urban | 4 | 4 | none |
| nyc_centre | 4 | 3 | `way_265424467` = 1.355% |
| nyc_rural | 4 | 4 | none |
| nyc_suburban | 4 | 3 | `way_846412106` = 0.913% |
| nyc_urban | 4 | 3 | `way_241862488` = 1.222% |

Every cell's median and mode is 0% (3 or 4 of 4 buildings are exactly zero in every cell — no
pooled headline is given per hard rule 5, and none would be informative here: the term is either
absent or ~1–1.8% of that one building's Total End Uses, never in between across this sample).
`dh_share_of_parser_total` (share of the parser's own `total_eui_kwh_m2 x floor_area_m2`, which
never includes District Heating — see D7) tracks `dh_share_of_total_end_uses` within ~0.02–0.03
percentage points for all 5 non-zero buildings (CSV columns `dh_share_of_total_end_uses`,
`dh_share_of_parser_total`). All 48 buildings parsed with `parser_status == "success"` through
`parse_building()` (`openubem/results/parser.py:716`); no failed parses, no fallback paths.

## CANDIDATE DEFECT

**The artifact is not universal across the 48 — it is bimodal, and the split does not look random.**
A quick survey of the 48 source IDFs (`step3_layout_assign/idfs/*.idf`) for the naming marker
`OpenUBEMUnknown` (present on `DHW_WaterUse_OpenUBEMUnknown`/`DHW_Heater_OpenUBEMUnknown`-style
object names) found it on only 3 of 48 IDFs, while 5 of 48 show non-zero District Heating — so the
marker is not a clean 1:1 predictor and this survey should not be read as a diagnosed rule. What is
established directly: at least one building with **zero** District Heating
(`way_328529693`, austin_centre) has a completely different DHW subsystem shape from
`way_1008727470` — a fully wired `SWHSys1` plant loop with `Pump:ConstantSpeed`, `Branch`,
`WaterHeater:Mixed`, and `WaterUse:Connections` properly connected via named nodes (source IDF
lines ~6544–6612), the kind of DOE-prototype-style HVAC template that is not the openUBEM
synthetic fallback. This is consistent with — but does not yet prove — a two-population
explanation: buildings whose DHW system comes from openUBEM's own synthetic builder (unconnected
`WaterUse:Equipment`/`Connections`, no plant) are exposed to the artifact; buildings that carry a
fully-specified template HVAC system (with its own wired SWH plant loop) are not. **This needs a
follow-up task to characterize properly** — this report does not attempt to enumerate which of the
48 (or the fleet) fall into each population; it only establishes that the split exists and is not
1-in-48, it is 5-in-48, with the artifact-carrying and non-carrying buildings visibly different in
IDF structure.

## What was not done, and why

- **T02 (production/`auto` sizing, 60-building stratified sample)** was **not** run. It is
  explicitly gated behind CP-1 by the plan (§7) and the plan's hard rule: "T02 does not start
  until CP-1 is signed." This report stops at CP-1 for the director to audit.
- **The CANDIDATE DEFECT's bimodal split was not fully characterized** (which of the 48, or what
  fraction of the fleet, carry the openUBEM-synthetic vs. template DHW subsystem) — that is
  outside T01's scope (mechanism + sizing on the 48 sample only) and is flagged above for the
  director to decide whether it becomes its own item.
- **No IDF edit was made in any repository file.** The one edit this plan authorised
  (§6 T01 step 2) was made on a scratch copy only (`scratchpad/open61_c2_experiment/`), never
  touching `scratchpad/open03-untrimmed-sample/` or any tracked file.
- **Parallelism was not used** — T01 runs only one EnergyPlus simulation pair (baseline/treated);
  the 6-concurrent-process cap (§4) applies to T02, not T01.

---

## T02

**T02 of `PLAN_five-items-2026-08-20-late.md`, redefined by CP-1 (§6b).** CP-1 signed D8/D9/D10:
the discriminator (`WaterUse:Equipment` `DHW_WaterUse_*` present + no `PlantLoop`) is exact on
all 48 T01 buildings, and **all 16,336** production IDFs match the non-zero side of it (D9). So
T02 no longer asks "does production carry it" — it sizes the term on re-simulated production
(`auto`) geometry, per cell.

Harness: `scripts/analysis/open61_production_sample_2026-08-20.py` (two phases, `select` then
`simulate`, run as two separate invocations so the selection froze to disk before any EnergyPlus
process started). Selection: `openubem/outputs/comparisons/open61_production_sample_selection.csv`
(60 rows — 5 per cell, `sort by osm_id, take every k-th` with `k = n_idfs_in_cell // 5`, starting
at index 0, no seed). Results: `openubem/outputs/comparisons/open61_production_sample.csv` (60
rows). Each building ran in its own working directory
(`scratchpad/open61_production_sample/<cell>/<idf_stem>/out/`) via `run_ep_isolated()`
(`scripts/analysis/open35_storey_intervention_2026-08-19.py:95`, imported by
`importlib.util.spec_from_file_location`, not copied), 6 concurrent workers max
(`ThreadPoolExecutor(max_workers=6)`). District Heating read exactly as T01
(`read_end_uses`/`check_c2`/`FUEL_COLUMNS`/`GJ_TO_KWH` imported from
`open61_district_source_2026-08-20.py`, not reimplemented). Production total read through
`parse_building()` (`openubem/results/parser.py:716`) with a `manifest_row` built from the
building's own row in `evidence/open48_refleet4/<cell>/results/05_results.csv` (real
`footprint_area_m2`/`levels`/`height_m`/`archetype_id`, not a dummy).

### Pre-registered controls, outcomes

- **C4 — rig reproduces the record.** All 60/60 within the 1.5% tolerance. Residual distribution
  (`|parser_total_eui_kwh_m2 − record_total_eui_kwh_m2| / record_total_eui_kwh_m2`, %): min
  0.0%, 25th pct 8.8e-15%, median 3.1e-14%, 75th pct 8.1e-14%, max 2.2e-7%, mean 8.5e-9%. The
  residual is machine-precision, not ~1%: `parse_building()`'s inputs here (`footprint_area_m2`,
  `levels`, `height_m`, `archetype_id`) came from the same `05_results.csv` row the record itself
  was computed from, and `resolve_simulated_floor_area()` picked the `eio_simulated` path on a
  freshly re-simulated `.eio` on both sides — this control shows the rig and the record agree to
  float noise, not that District Heating is small (it is not; see below). It does **not** by
  itself bound the district-heating term, because `parse_building()`'s own total never includes
  District Heating (D7) — C4 proves the rig is faithful, not that the term is negligible.
- **C4b — discriminator holds on production.** **60/60 non-zero.** No building broke the
  discriminator; D8 extends cleanly from the 48-sample census to re-simulated production
  geometry.
- **C5 — EnergyPlus version.** `Program Version,EnergyPlus, Version 23.1.0-87ed9199d4` read from
  each of the 60 `.err` files (5 distinct timestamp suffixes, one version string). First run:
  `scratchpad/open61_production_sample/austin_centre/relation_13781131/out/eplusout.err`.
- **C6 — no cross-contamination.** SHA-256 of `austin_centre/relation_13781131/out/eplusout.sql`
  (`5f9354a2...`) vs `austin_centre/way_135049621/out/eplusout.sql` (`01d0ada1...`) — different.
  No OPEN-58 reproduction.

### Per-cell sizing (12 cells, n=5 each, no pooled number)

| Cell | median share of Total End Uses | share range | median kWh/m² missing | kWh/m² range |
|---|---|---|---|---|
| austin_centre | 1.01% | 0.90–1.46% | 1.67 | 1.14–1.68 |
| austin_rural | 1.23% | 1.05–19.96% | 1.18 | 1.18–29.97 |
| austin_suburban | 0.96% | 0.69–7.16% | 1.16 | 1.12–17.32 |
| austin_urban | 1.22% | 0.71–2.21% | 1.17 | 1.06–5.30 |
| la_centre | 1.68% | 1.19–1.77% | 2.16 | 1.23–2.63 |
| la_rural | 1.16% | 0.78–17.31% | 1.24 | 0.52–31.76 |
| la_suburban | 22.51% | 18.66–24.02% | 32.25 | 31.33–32.78 |
| la_urban | 22.37% | 1.80–23.80% | 31.42 | 2.63–32.53 |
| nyc_centre | 1.42% | 0.79–18.78% | 1.40 | 0.64–41.20 |
| nyc_rural | 1.23% | 1.07–14.93% | 1.50 | 1.49–89.12 |
| nyc_suburban | 1.01% | 0.84–14.74% | 2.89 | 1.47–37.29 |
| nyc_urban | 1.04% | 0.78–2.52% | 1.40 | 1.40–2.80 |

`kWh/m² missing` = `dh_total_kwh / parser_floor_area_m2`, both columns in
`open61_production_sample.csv`; `parser_floor_area_m2` is `resolve_simulated_floor_area()`'s own
denominator (`eio_simulated` on all 60), the same denominator `total_eui_kwh_m2` uses. "Missing"
means: this energy is real (booked to District Heating by EnergyPlus) but is absent from
`parse_building()`'s `total_eui_kwh_m2` because `METER_QUERY` (`parser.py:42`) does not name a
district meter (D7) — it is not part of C4's residual either way.

### CANDIDATE DEFECT — the term is bimodal across the 60, not uniformly ~1%, and the high mode is far larger than anything T01's 48-sample saw

Sorted by `dh_kwh_m2`, the 60 split cleanly: **43 of 60 sit at 0.5–5.3 kWh/m²** (≈0.7–2.5% share,
the range T01's 5/48 non-zero sample also showed), and **17 of 60 sit at 17.3–89.1 kWh/m²**
(≈4.6–24.0% share) — no building in between. T01's 48-sample never saw a value above 1.8% share;
this 60-sample's high mode is **10–20x larger**. The high mode is not one cell's artifact: it
appears in 8 of the 12 cells (`austin_rural` 1/5, `austin_suburban` 1/5, `la_rural` 1/5,
`la_suburban` **5/5**, `la_urban` 4/5, `nyc_centre` 1/5, `nyc_rural` 2/5, `nyc_suburban` 2/5) —
absent only from `austin_centre`, `la_centre`, `austin_urban`, `nyc_urban`. `la_suburban` and
`la_urban` are the extreme case: 9 of their combined 10 buildings are in the high mode, at a
strikingly tight 28.1–32.8 kWh/m² band (`la_urban`'s one exception, `way/402036185`, sits at 2.63
kWh/m², the low-mode range). This needs a follow-up task to characterize (building size class,
archetype, or DHW peak-flow-rate scale look like candidate drivers given the tight clustering of
the high-mode values) — this report only establishes that the split exists, is not
cell-determined alone, and dwarfs what the 48-sample census suggested the term's ceiling was.

### What was not done, and why

- The high/low split's driver (building size, archetype, DHW peak flow rate, or something else)
  was **not** diagnosed — outside T02's scope (sizing only, per §6b's redefinition), flagged
  above for the director.
- No comparison was made against the deleted run-4 `.sql` corpus's own District Heating column
  (fact D1: it no longer exists) — this task's `.sql` files are the only district-heating read
  available for these 60 osm_ids on production geometry; C4 is the only cross-check against the
  surviving record (`05_results.csv`), and `05_results.csv` was itself produced without a
  district meter (D7), so it cannot corroborate the district-heating figure, only the parser total.
- Only 60 of 8,160 production buildings were sampled, per the plan (§6 T02 step 4: "60 of 8,160,
  stratified, not a census"). The bimodal split's population fractions above (43/60, 17/60) are
  this sample's counts, not a fleet-wide estimate — no fleet-wide count is claimed here.
