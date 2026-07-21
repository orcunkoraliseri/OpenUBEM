# Fusion test-fixture manifest (T12.5 license/bundle guard)

Small, synthetic, offline-test-only slices — never a city-wide/global dataset
(M07 §2 licence/bundle verdict; plan §6 T12.5). Each row lists the bundled
fixture, what it stands in for, and its allowlisted license class.

| file | source | license | size_bytes |
|---|---|---|---|
| overture_testcell_slice.parquet | synthetic, mimics the Overture Buildings GeoParquet schema (T12.2 offline test fixture) | CDLA-Permissive-2.0 | 15647 |
| lidar_testcell_ndsm.tif | synthetic, mimics a USGS 3DEP nDSM zonal raster clip (T12.3 offline test fixture) | public-domain | 10386 |
| assessor_testcell.gpkg | synthetic, mimics a municipal assessor parcel extract (T12.3 offline test fixture) | public-domain | 98304 |
| overture_nyc_centre_slice.parquet | REAL Overture Buildings theme, release 2026-06-17.0, bbox-clipped to the nyc_centre fixture cell (T12.6 CP-4 LIVE_SMOKE) | CDLA-Permissive-2.0 | 279284 |
