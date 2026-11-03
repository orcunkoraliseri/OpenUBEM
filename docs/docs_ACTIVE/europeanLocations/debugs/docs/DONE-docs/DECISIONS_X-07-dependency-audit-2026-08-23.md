# X-07 execution dependency audit

Date: 2026-08-23

The local X-07 environment has no `cdsapi`, `pvlib`, or `xarray` package and
no `C:\Users\o_iseri\.cdsapirc` CDS credentials file.  Consequently the
required ERA5 download, licence-at-download capture, conversion, and six-gate
EPW validation cannot be performed or represented as complete.

The ruled station/window metadata remains valid, but no EPW file or weather
registry may be marked acquired.  This is an execution dependency block, not
a change to D-EU-05.

## Update (2026-08-23)

The approved dependencies are now installed in `.venv`: `cdsapi 0.7.7`,
`pvlib 0.15.2`, and `xarray 2026.7.0` (evidence:
`openubem/outputs/eu_evidence/X-07/dependency_installation.log`). No
`C:\\Users\\o_iseri\\.cdsapirc` or `CDSAPI_KEY` is present, so live ERA5
acquisition remains blocked solely by credentials. No weather artefact has
been claimed as acquired.
