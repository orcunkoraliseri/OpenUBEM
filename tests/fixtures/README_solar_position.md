# `solar_position_reference.csv` provenance

**Source:** NOAA Global Monitoring Laboratory Solar Calculator spreadsheet,
`NOAA_Solar_Calculations_day.xls`, downloaded from
`https://gml.noaa.gov/grad/solcalc/NOAA_Solar_Calculations_day.xls` (linked from
`https://gml.noaa.gov/grad/solcalc/calcdetails.html`, which states the calculations are
"based on equations from *Astronomical Algorithms*, by Jean Meeus" — the same NOAA/Michalsky-
family algorithm PLAN T04 specifies).

**Retrieved:** 2026-07-23.

**How the table was generated.** The downloaded `.xls` is a real Microsoft Excel workbook with
live formulas (author: Chris Cornwall / NOAA). It was opened with Excel via COM automation
(`scratchpad/gen_solar_reference.ps1`), the input cells `B3` (Latitude), `B4` (Longitude), `B5`
(Time Zone), `B7` (Date, Excel serial) were set for each of 14 scenarios spanning both solstices,
both equinoxes, both hemispheres, the equator, the tropic of Cancer, a high latitude (65 N,
including a below-horizon winter case), and a real named site (NYC), then the workbook was fully
recalculated (`Application.CalculateFullRebuild`) and two rows were read back per scenario — the
row nearest local-clock time 12:00 and nearest 09:00 (column `E`, "Time (past local midnight)",
6-minute grid) — reading columns `T` (Sun Declin), `AE` (Solar Elevation Angle, uncorrected),
`AG` (Solar Elevation Angle corrected for atmospheric refraction), `AH` (Solar Azimuth Angle,
deg clockwise from N). This is the actual official spreadsheet computing the actual official
formula chain for each scenario — not a hand re-derivation.

**Units in the CSV:**
`date_serial` = Excel serial date (days since 1899-12-30); `time_frac` = fraction of the
24-hour civil day at the given `tz` (hours, + = east); `elevation_deg` = refraction-corrected
solar elevation (what `solar_position()` should reproduce); `azimuth_deg` = clockwise from
true north; `declination_deg` = solar declination for cross-checking intermediate values.

**How the test consumes it.** `test_microclimate_solar.py` converts
`(date_serial, time_frac, tz)` to a UTC timestamp (`solar.py`'s binding input convention —
see its module docstring) and calls `solar_position(dt_utc, lat, lon)`, comparing against
`elevation_deg` / `azimuth_deg` at the plan's ±0.1° gate.
