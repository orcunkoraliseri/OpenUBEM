# Decision request — EU-07 Lyon–Bron OneBuilding EPW candidate

**Date:** 2026-08-25  
**Status:** `RULED (OB1 selected)`  
**Scope:** Whether a user-directed OneBuilding Lyon–Bron TMYx EPW may replace
or supplement the currently ruled direct ERA5/CDS weather path for the EU-04
S2 short-period simulation.

## Candidate acquired at user direction

Downloaded from the OneBuilding France catalogue:

- catalogue: `https://climate.onebuilding.org/WMO_Region_6_Europe/FRA_France/index.html`
- archive: `FRA_AR_Lyon-Bron.AP.074800_TMYx.2011-2025.zip`
- extracted EPW: `FRA_AR_Lyon-Bron.AP.074800_TMYx.2011-2025.epw`
- location header: `Lyon-Bron.AP`, WMO `074800`, 45.72610 N / 4.93780 E,
  UTC+1, 198 m
- stored candidate directory:
  `openubem/data/weather/candidates/onebuilding_lyon_bron_tmyx_2011_2025/`
- archive SHA-256:
  `83f4fcb23af0490f54c81b3b4f0a41ff83dbb8a557baada0cdbcfe3d77bae76d`
- EPW SHA-256:
  `07b267d70894d32dc0f9544f6023996a3460d4963df7ec56d3477f02cf77928`

The EPW `COMMENTS 1` identifies it as an `NCEI ISD/ERA5` TMYx composite with
one typical month selected from each month across 2011–2025. It is therefore
not a continuous observed year and must never be labelled as actual
2011–2025 weather.

## Measured validation state

The file has a valid `LOCATION` header and exactly 8,760 rows; its required
fields have no missing-value sentinel. It does **not** pass the existing
project DR08 gate 4: with the repository's stated solar-position method,
3,389 of 4,443 daytime rows exceed the 5 W/m² closure tolerance for
`GHI = DHI + DNI × cos(zenith)`. The maximum error is 132.834 W/m², p95 is
100.071 W/m², and mean is 35.568 W/m². Gate 5 national monthly benchmark and
gate 6 EnergyPlus smoke are not run.

This is a candidate finding, not a weather approval. The active
`weather_registry.json` still rules direct ERA5 via CDS/PVLib and remains
unchanged.

## Decision

### D-EU-07-OB-LYO — OneBuilding candidate use

Choose one:

- **OB1 — retain as candidate only (recommended):** keep the downloaded EPW
  for comparison and local diagnostics. Do not add it to the approved weather
  registry or run S2 against it. Continue to require the ruled CDS/ERA5 path.
- **OB2 — authorize a separate TMYx evaluation track:** add it under a new,
  explicitly labelled `ONEBUILDING_TMYX_CANDIDATE` status for non-promotional
  controlled runs only. Before any S2 result is claimed, define an approved
  solar-consistency criterion for this source and pass source-specific gates
  5 and 6. It remains distinct from actual-weather validation.
- **OB3 — replace the CDS/ERA5 path for S2:** authorize a material weather
  source-method change. This requires an amended registry contract, provenance
  and licence capture, source-specific validation gates, and a declaration
  that S2 uses TMYx typical-year weather rather than actual weather.

**Owner answer:** `D-EU-07-OB-LYO = OB1 (retain as candidate only)`

## Execution boundary

No registry rewrite, no gate-threshold change, no S2 simulation, and no energy
result is authorized until this ruling is recorded.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-25

