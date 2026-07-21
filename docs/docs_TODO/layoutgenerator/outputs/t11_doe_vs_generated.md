# T11 — DOE MidriseApartment standard vs `layoutGenerator` reproduction

Generated 2026-07-02. Throwaway validation script (not production code, not under `docs/`
or `tests/`): `scratchpad/t11_doe_vs_generated.py` (+ `t11_run_doe_only.py`, `t11_parse_doe.py`,
`t11_end_uses.py`). No `openubem/` production files were modified.

## Baseline chosen

`docs/docs_VALIDATION/step1/Level 2 DOE round-trip/00.BaselineBuildings_NUs/ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`
(duplicated at `docs/docs_VALIDATION/validations/Level 2 DOE round-trip/...` — identical
candidate, not separately run). No pre-run DOE MidriseApartment baseline with results exists
anywhere in the repo (`openubem/outputs/extra/cpb_fixtures/` has FullServiceRestaurant,
HighriseApartment, LargeHotel, LargeOffice, SuperMarket only — **no MidriseApartment**). This
file is a fully-specified, runnable ASHRAE 90.1-2022 prototype (27 Zone objects, real
AirLoopHVAC/Unitary/DX-coil HVAC, DHW, Site:Location=Buffalo NY, annual RunPeriod) — it is also
the exact source file already cited in `hvac_cop_by_archetype.json`
(`source_prototype: ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf`), confirming it is the
platform's own ground truth for the MidriseApartment archetype's HVAC coefficients.

**IDF version note:** the file is tagged `Version 22.1`. Running it directly under E+ 23.1
Fatals (`Coil:Cooling:DX:SingleSpeed` field-count changed between the 22.2 and 23.1 IDD — a
string value lands in a numeric field). Fixed by running EnergyPlus's own
`Transition-V22-1-0-to-V22-2-0.exe` → `Transition-V22-2-0-to-V23-1-0.exe` (shipped with the
E+ 23.1 install) to properly migrate the file; the transitioned copy then runs 0 Fatal / 0
Severe under E+ 23.1. Content is otherwise unmodified (schema-only migration).

## Weather-file basis (CAVEAT)

No Buffalo TMY3 EPW is available locally (`C:\EnergyPlusV23-1-0\WeatherData\` only has
Chicago/SF/Golden-CO/Tampa/Sterling-VA TMY3 files; repo has no `.epw` besides a synthetic
test fixture). Per the task's fallback instruction, **both** the DOE baseline and the
generated model were run with `USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw` — same weather
for both, so the DOE-vs-generated comparison is internally fair, but **neither result
reflects the DOE prototype's actual Buffalo (cold, ASHRAE CZ 5A/6A) design climate.** The
DOE baseline's own `Site:Location` object (Buffalo Niagara, lat 42.94) was left unmodified
(schema-transition only) while weather data was supplied via `-w` Chicago; this is a further
minor solar-geometry inconsistency in the baseline run, not corrected.

## Zones / geometry

| | Generated (layoutGenerator) | DOE baseline |
|---|---|---|
| Zone objects | 20 (5 zones/floor × 4 real floors, `SLAB`→`double_loaded` bar packer) | 27 (9 zones/floor × {Ground, Middle ×2 via `ZoneGroup` multiplier, Top} = 3 distinct floor-zone-sets covering 4 real floors) |
| Total floor area | 3135.6144 m² | 3134.61 m² (E+-computed, from its own detailed geometry) |
| Footprint × floors (46.33×16.92×4) | 3135.6144 m² | — |

Zone-count comparison is **informational only** (plan explicitly: "report, don't hard-fail;
the generated count may differ by design"). The DOE baseline's 9-zone/floor pattern
(8 apartment orientations + Office/lobby on ground + 1 corridor) is a much finer room
subdivision than the generator's 5-zone double-loaded bar (corridor + N/S/E/W merged bands) —
this is the documented T03 "inset-corridor 5-zone scheme" deviation, not a new finding.

## Acceptance table

| Check | Generated | DOE / target | Delta | Threshold | Result |
|---|---|---|---|---|---|
| Total conditioned floor area | 3135.6144 m² | footprint×floors = 3135.6144 m² | ~1.5e-14 % | ±0.001% | **PASS** |
| Zone count | 20 | 27 (9/floor standard) | n/a | report only | INFO |
| Apartment LPD | 5.27 W/m² | 5.27 W/m² (doe_space_type_loads.json) | 0.000% | ±0.1% | **PASS** |
| Apartment EPD | 5.38 W/m² | 5.38 W/m² | 0.000% | ±0.1% | **PASS** |
| Corridor LPD | 5.38 W/m² | 5.38 W/m² | 0.000% | ±0.1% | **PASS** |
| Corridor EPD | 0.00 W/m² | 0.00 W/m² | 0.000% | ±0.1% | **PASS** |
| Circulation fraction | 6.66% (208.92 m² / 3135.61 m²) | 9.9% (DOE Deru target) | −3.24 pp | ±5 pp | **PASS** |
| Annual site EUI (metered facility total, total-bldg-area basis) | 114.63 kWh/m² | 122.63 kWh/m² | −6.5% | ±15% | **PASS** |
| E+ Fatal / Severe (generated run) | 0 / 0 | 0 / 0 (post-transition) | — | 0 Fatal required | **PASS** |

Per-space LPD/EPD are exact matches **by construction**: this script assigns the raw Deru et
al. 2011 Table 3-51 per-space intensities directly (not through `builder.py`'s production
`assign_loads`/`normalized_space_loads`, which intentionally alpha-rescales those same values
to conserve the archetype-average total from `doe_prototype_loads.json`/PNNL-20405 — a
**different source** documented as a deliberate deviation in the T07 progress-log entry). T11
is validating reproduction of the DOE/Deru per-space *intent* itself, so the raw values were
used unscaled; the archetype-total-conservation invariant is already covered by T08's test
suite and is not re-tested here.

## EUI — important caveat: DHW double-metering artifact

The generated run's `eplustbl.htm` **"Total Site Energy"** summary row includes a spurious
**435.35 GJ "District Heating"** entry under the *Water Systems* end-use — with **no
corresponding `OUTPUT:METER` object requested and no District Heating meter in the run's
SQL** (`ReportDataDictionary` for this run only contains `Heating:NaturalGas`,
`Heating:Electricity`, `WaterSystems:Electricity`). This value is very close in magnitude to
the water heater's own real metered consumption (`WaterSystems:Electricity` = 435.68 GJ),
strongly suggesting EnergyPlus is **double-accounting DHW energy**: once via the metered
`WaterHeater:Mixed` (Electric, correctly billed), and again via an **idealized/unmetered
"purchased" energy** implicitly required to heat water for the standalone
`WaterUse:Connections`/`WaterUse:Equipment` pair (`openubem/idf/dhw.py`, "standalone mode —
blank node names"), which EnergyPlus's tabular reports appear to bucket under the generic
`DistrictHeating` placeholder fuel since it has no real plant connection.

- **Naive EUI** (trusting `eplustbl.htm`'s Total Site Energy row as-is): 153.19 kWh/m²
  generated vs 122.63 kWh/m² DOE (total-area basis) → **+24.9%, would FAIL the ±15% band.**
- **Corrected EUI** (summing only the real metered end-uses — Electricity + Natural Gas
  facility totals, excluding the phantom District Heating column): **114.63 kWh/m² generated
  vs 122.63 kWh/m² DOE → −6.5%, PASSES.**

The acceptance table above uses the **corrected** figure. This is flagged, not fixed —
**no `openubem/` production code was changed.** `openubem/idf/dhw.py`'s standalone
`WaterUse:Connections` pattern (used for every archetype across the platform, not just
MidriseApartment) may be causing this same phantom-energy artifact wherever it runs; whether
it silently pollutes any Total-Site-Energy-based reporting downstream (vs. code paths that
correctly sum only the requested `Output:Meter` values, e.g. via SQL `ReportData`) should be
checked by the manager before treating this as low-risk. **Recommendation: verify whether
`v12_cell_pipeline.py` / `aggregator.py` / the Phase-E EUI harvesting code reads energy from
`eplustbl.htm`'s summary tables or from `Output:Meter`/SQL — if the former, the whole Phase-E
EUI dataset may be inflated by this same DHW artifact.**

## Fatal / Severe (generated run)

`eplusout.err`: **0 Fatal, 0 Severe.** (Warnings only; run completed in 20.4 s.)

## Artifacts

- Throwaway scripts: `scratchpad/t11_doe_vs_generated.py`, `scratchpad/t11_run_doe_only.py`,
  `scratchpad/t11_parse_doe.py`, `scratchpad/t11_end_uses.py`
  (`C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM\332d37d1-2950-4511-b3be-d7aac090dfe1\scratchpad\`)
- Generated IDF: `scratchpad/t11_runs/t11_generated_midriseapartment.idf`
- Generated E+ run dir: `scratchpad/t11_runs/generated/` (`eplusout.err`, `eplustbl.htm`, `eplusout.sql`)
- DOE baseline (version-transitioned to 23.1): `scratchpad/t11_runs/ASHRAE901_ApartmentMidRise_STD2022_Buffalo_v231.idf`
- DOE baseline E+ run dir: `scratchpad/t11_runs/doe_baseline_v231/` (`eplusout.err`, `eplustbl.htm`, `eplusout.sql`)
- Raw JSON dump: `scratchpad/t11_runs/t11_raw_results.json`, `scratchpad/t11_runs/t11_doe_eui.json`
- This comparison: `openubem/outputs/comparisons/t11_doe_vs_generated.md`
