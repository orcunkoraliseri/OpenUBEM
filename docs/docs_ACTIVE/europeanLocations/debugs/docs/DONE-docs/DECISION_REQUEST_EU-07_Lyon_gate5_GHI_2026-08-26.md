# Decision request: EU-07 Lyon-Bron DR08 gate 5 solar benchmark

**Status:** RULED — G5-A exception approved 2026-08-26

## Ruling

The owner approved promotion with a documented exception: 11/12 monthly GHI checks pass the 10% limit and the annual GHI difference is 3.2%; November differs by 13.8% and is retained as an explicit deviation. Gate 6 passes with zero severe errors. The Lyon EPW may be promoted for EU-04 S2 weather use.

## Measured state

- The direct ERA5 Lyon-Bron 2023 EPW passes DR08 gates 1–4.
- EnergyPlus 23.1 smoke passes with return code 0 and zero severe errors (gate 6).
- Lyon-Bron station monthly mean temperatures are available and differ from ERA5 by at most 1.25 K, within the DR08 ±1.5 K limit.
- The Lyon-Bron station source provides sunshine duration, but no monthly GHI series. The DR08 gate requires `|Delta GHI| <= 10%`; sunshine duration is not GHI and has not been substituted.

## Options

1. **G5-A (recommended):** approve an independent, publication-compatible satellite/reanalysis monthly GHI benchmark at the same Lyon-Bron coordinates, while retaining the Météo-France station for temperature validation. This preserves a measured solar comparison without mislabelling sunshine duration as GHI.
2. **G5-B:** retain the strict national-station GHI requirement and keep the EPW out of the registry until Météo-France supplies a monthly radiation series.
3. **G5-C:** revise DR08 to accept station sunshine duration as a solar proxy. This changes the adopted acceptance rule and requires explicit owner approval; it is not recommended.

## Current consequence

Until G5-A or G5-B is ruled, the EPW remains candidate-only, `weather_registry.json` is unchanged, and EU-04 S2 does not launch.

Evidence: `openubem/outputs/eu_evidence/EU-07/era5_lyon_bron_weather_gates_2026-08-26.md`.
