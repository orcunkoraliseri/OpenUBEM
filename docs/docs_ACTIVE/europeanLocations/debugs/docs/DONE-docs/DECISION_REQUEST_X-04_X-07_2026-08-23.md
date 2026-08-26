# Decision request: unblock X-04 and X-07

Date: 2026-08-23  
Prepared for: project review

## Purpose

Two execution slices cannot be accepted without an evaluator decision or
project-owned access.  This packet gives the reproducible observations and
the smallest decision needed for each slice.  It does not alter any accepted
project ruling.

## X-04 — EU-03 EnergyPlus numeric fixture R5

### Requirement being tested

DR11 fixture R5 specifies a 1 m2 `Material:NoMass` surface with `U = 2.0`
W/(m2 K), exterior temperature 0 C, zone air at 20 C, and
`SurfaceProperty:OtherSideCoefficients` with:

```text
External Dry-Bulb Temperature Coefficient = 0.5
Zone Air Temperature Coefficient          = 0.5
```

Its literal pass criteria are:

```text
Surface Inside Face Conduction Heat Transfer Rate = 20.000 W +/- 0.001 W
Surface Outside Face Temperature                  = 10.000 C +/- 0.001 C
```

### Reproducible observation

Environment: local EnergyPlus 23.1.0 (`C:\EnergyPlusV23-1-0\energyplus.exe`).

Command:

```powershell
.venv\Scripts\python.exe -m pytest -q tests\test_eu_physics_primitives.py tests\test_eu_physics_energyplus.py
```

Result:

```text
5 passed, 1 xfailed
```

The saved-IDF tests pass: realised NoMass U equals `U + delta_U`, declared
`InternalMass` capacity equals `c_m * A_floor`, and the saved coefficients
are 0.5/0.5.  The engine-level R5 fixture completes successfully and reports:

```text
Surface Outside Face Temperature                  = 10.000 C
Surface Inside Face Conduction Heat Transfer Rate = 19.993496 W
```

The 0.006504 W difference is consistent with the EnergyPlus inside-film
resistance remaining in the reported conduction result.  A very large
user-specified inside convection coefficient did not remove that residual.
The R5 test is intentionally a strict expected failure: the requirement has
not been weakened to make the suite green.

### Decision requested

Select one of the following, recording the basis:

1. Accept an EnergyPlus-aware R5 criterion that compares the reported state
   including its inside film, while retaining the exact 10.000 C other-side
   temperature check; or
2. Provide/approve an alternative EnergyPlus formulation that removes the
   inside-film effect and demonstrably meets 20.000 W +/- 0.001 W; or
3. Retain the literal criterion and leave X-04 blocked.

R3 and R7 must still be implemented after this R5 decision; they are not
claimed complete by this packet.

Evidence:

- `openubem/outputs/eu_evidence/X-04/targeted_pytest_partial.log`
- `tests/test_eu_physics_energyplus.py`
- `debugs/docs/DONE-docs/DECISIONS_X-04_R5-engine-film-2026-08-23.md`
- `DeepResearch/DR11_tabula_to_dynamic_simulation_translation.md` §4.3

## X-07 — EU-07 ERA5 weather registry and acquisition

### Requirement being tested

X-07 must download ERA5 single-level data for the ruled station/windows,
convert it to EPW, capture the CDS-served licence text at download time, and
run the six DR08 validation gates.

| Fold | Station | Weather window |
|---|---|---|
| `es` | Madrid, WMO 08221 | 2009–2010 |
| `uk` | London Heathrow, WMO 03772 | 2014–2015 |
| `it` | Bologna Borgo Panigale, WMO 16140 | 2013–2014 |

The exact 12-month selection remains `RULED_NOT_PINNED` until the Step 7
diary dates are available; that is expected and does not itself prevent the
two-year source acquisition.

### Reproducible environment audit

The local `.venv` has none of the required packages:

```text
cdsapi = absent
pvlib  = absent
xarray = absent
```

No project-user CDS credential file exists at:

```text
C:\Users\o_iseri\.cdsapirc
```

Without the credential, ERA5 retrieval and the required capture of licence
text actually served by CDS cannot be performed.  No weather file, checksum,
or validation result is therefore claimed.

### Decision/action requested

Provide project-authorised CDS API credentials/configuration and approve
installation of the required packages in `.venv`, or retain X-07 as blocked.
The needed package set is:

```text
cdsapi
pvlib
xarray
```

Once access is available, the next work is deterministic: retrieve the ruled
data, write the EPW and registry files, preserve SHA-256 hashes and CDS
licence text, then execute the six-gate validation suite.

Evidence:

- `debugs/docs/DONE-docs/DECISIONS_X-07-dependency-audit-2026-08-23.md`
- `DeepResearch/DR08_actual_year_weather_sources_and_licences.md` §6
- `WALKTHROUGH_european_locations.md` §12.6

## Current acceptance state

| Slice | Status | What would unblock it |
|---|---|---|
| X-04 | `ACCEPTED` | Complete: R3 (free-float natural decay), R5 (0.5/0.5 b-factor), R7 (0.85 F_red scaling), and analytical primitives all pass (9/9). |
| X-07 | `BLOCKED` | Awaiting project-owned CDS credentials in `~/.cdsapirc`, followed by ERA5 acquisition and 6-gate validation. |

## Resolution record — 2026-08-23

The evaluator accepted X-04 option 1 for R5 and option R3-A / R3-B for R3:
- **R5** uses the approved EnergyPlus-aware acceptance band of $\pm 0.01\text{ W}$ and $\pm 0.01\text{ }^\circ\text{C}$; local EnergyPlus test passes.
- **R7** is implemented and passes the required $0.8500 \pm 0.0001$ heating-ratio criterion.
- **R3** root cause was diagnosed (artificial $10^7$ convection override causing numerical solver locking); natural convection fixture was adopted, producing continuous physical thermal decay ($T(14.04\text{h}) \approx 3.6\text{ }^\circ\text{C}$, $T(24\text{h}) \approx 1.6\text{ }^\circ\text{C}$). Normative 1-node analytical math is verified in `test_eu_physics_primitives.py`. All 9 tests pass.

For **X-07**, installation of `cdsapi`, `pvlib`, and `xarray` in `.venv` was approved and completed. Acquisition remains cleanly blocked on project-owned CDS credentials (`~/.cdsapirc` or `CDSAPI_KEY`). No synthetic weather files are fabricated.
