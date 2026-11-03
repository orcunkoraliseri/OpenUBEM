# `utci_reference_table.csv` provenance

**Gate:** `test_microclimate_utci.py::test_reference_table_atol_1e-6` — `atol = 1e-6 degC`.
This tests a **transcription** of the official 210-coefficient Bröde polynomial, which must
be exact, not a physical model (PLAN §4.5).

**How the table was built.** `openubem/microclimate/utci.py` transcribes the polynomial
directly from the *primary* source: `UTCI_a002.f90` (Peter Bröde, COST Action 730, Version a
0.002, October 2009), downloaded from `https://www.utci.org/resources/UTCI%20Program%20Code.zip`
(linked from the official https://www.utci.org/ homepage) on 2026-07-23.

The reference values in this CSV were computed by a **second, independently-authored**
transcription of the same official polynomial — `pythermalcomfort.models.utci._utci_optimized`
(https://github.com/pythermalcomfort/pythermalcomfort, MIT licence,
`pythermalcomfort/models/utci.py`, retrieved 2026-07-23) — copied verbatim (its `@numba.vectorize`
decorator stripped, since numba has no Python 3.14 wheel here, F-19) into
`scratchpad/gen_utci_reference_table.py` and evaluated at 42 points spanning the polynomial's
valid domain (`Ta` [-50,50], `Tmrt-Ta` [-30,70], `va10` [0.5,17], `e` [0,5] kPa): the CP-1
sanity row (`Tmrt=Ta`, `va10=0.5 m/s`, `RH=50%`, `Ta in {-20,0,20,40}`), a hand-picked grid
covering the corners and centre of the domain, and 20 seeded-random (`numpy.random.default_rng(42)`)
in-domain points.

**Why two independently-authored transcriptions, not one "official" numeric table.** No
ready-made high-precision (>1 decimal) published reference table for arbitrary inputs could be
located online (the official `utci.org` site ships only *code*, and its compiled demo
`UTCI_a002.exe` prints results rounded to 1 decimal place — too coarse for `atol=1e-6`). Two
transcriptions independently derived from the same official coefficients, written in different
code styles by different people (one from the raw Fortran term order, one previously audited and
used in a widely-depended-on open-source package), agreeing to `1e-6 degC` across 42 points is
strong evidence against a coefficient-transcription error — the exact failure mode this gate
exists to catch (PLAN §4.1). A coarser, execution-based cross-check against the actual compiled
official `UTCI_a002.exe` binary (rounded to 0.1 degC) is reported separately at CP-1.

**Columns:** `ta_c`, `tmrt_c`, `va10_ms` (10 m wind, the polynomial's own argument — §4.2),
`e_kpa` (vapour pressure, kPa — §4.4), `utci_expected_c`, `label` (`reference_env_rh50` /
`grid` / `random`).
