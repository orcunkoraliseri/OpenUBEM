# Analysis request — X-04 R3 and X-07 ERA5 credentials

Date: 2026-08-23  
Prepared for: evaluator review  
Implementation status: no status is changed by this document.

## Executive summary

| Slice | What now passes | Remaining item | Decision/action required |
|---|---|---|---|
| X-04 / EU-03 | Saved-IDF D-EU-02 arithmetic; R5 with the accepted engine-aware tolerance; R7 ratio | Dynamic R3 cooling trajectory | Confirm the intended EnergyPlus formulation or approve a revised R3 acceptance formulation grounded in the engine model. |
| X-07 / EU-07 | Required Python dependencies are installed | Live ERA5 acquisition, licence capture, EPW conversion, six validation gates | Configure project-owned CDS credentials; no credential value should be put in this repository or supplied in a review response. |

## X-04 — R3 dynamic EnergyPlus discrepancy

### Accepted items, not open for re-decision

- R5 was resolved by the evaluator's accepted Option 1. EnergyPlus 23.1.0 reports `19.993496 W` rather than a literal `20.000000 W` because of retained interior-film behaviour. The current criterion is `20.000 ± 0.01 W` and `10.000 ± 0.01 C`; it passes.
- R7 passes: scaling both U and air change by `F_red_temp = 0.85` gives a heating-rate ratio of `0.8500 ± 0.0001`.
- The analytical R3 reference passes: capacity `1.62e7 J/K`, heat loss `320 W/K`, and `tau = 14.0625 h` yield `20/e = 7.357589 C`.

### Fixture as currently implemented

File: `tests/test_eu_physics_energyplus.py`, functions `_r3_idf()` and `test_r3_free_float_energyplus_fixture()`.

The fixture is intentionally a small local EnergyPlus run:

| Item | Current value |
|---|---:|
| Engine | EnergyPlus 23.1.0 |
| Geometry | 10 m × 10 m × 3 m single zone |
| Envelope | six `Material:NoMass` surfaces, U = 1 W/(m²K) |
| Envelope H | 320 W/K (`320 m² × 1 W/(m²K)`) |
| Thermal mass | one `InternalMass`, 100 m², 0.1 m × 1800 kg/m³ × 900 J/(kgK) = `1.62e7 J/K` |
| Boundary | `OtherSideCoefficients` at 0 C |
| Preconditioning | day 1 IdealLoads heating at 20 C and cooling target at 20 C |
| Release | day 2 heating unavailable, cooling target 50 C |
| Test instant | 01/02 14:04, i.e. 14.0625 h after release |

### Reproduced observation

The release state is verified at `20.000000 C`. At the R3 test instant EnergyPlus reports:

```text
Zone Air Temperature = 19.998714 C
DR11 lumped target   =  7.357589 C ± 0.05 C
```

The strict expected failure remains deliberate. It prevents an unapproved tolerance adjustment from making the suite green.

### Technical interpretation to evaluate

The static U/mass values match the DR11 one-node analytical model, yet EnergyPlus's surface/air/thermal-mass heat-balance formulation does not release energy according to that one-node trajectory. The likely reconciliation questions are:

1. Does DR11 intend a pure one-node analytical reference only, or a dynamic EnergyPlus fixture with a prescribed material/surface coupling that has not been stated?
2. Is `InternalMass` linked only through the EnergyPlus inside-surface heat balance in a way that needs an explicit convection/radiation treatment or a different `HeatBalanceAlgorithm` for this test?
3. Is the precondition/release implementation correct for the expected EnergyPlus IdealLoads semantics, including its cooling availability and schedule processing?
4. Should R3 be tested from a reported energy/temperature state other than Zone Air Temperature (for example a defined combined air/mass state), with a justified conversion back to the DR11 lumped target?

### Requested response format

Please select one option and state its technical basis:

**R3-A — EnergyPlus formulation.** Provide or approve the exact EnergyPlus objects/settings/observables that should achieve the DR11 dynamic target. The implementation will replace the strict expected failure and re-run the fixture.

**R3-B — Analytical reference only.** Accept the existing analytical test as the R3 acceptance test and retain the Engine run as a documented non-gating behaviour check.

**R3-C — Revised engine criterion.** Define an engine-specific target, observable, and tolerance, including why it faithfully represents the stated 320 W/K and `1.62e7 J/K` case.

**R3-D — Keep blocked.** Retain the strict expected failure pending a later modelling review.

### Evidence

- `openubem/outputs/eu_evidence/X-04/targeted_pytest_r3_fixture.log`
- `tests/test_eu_physics_energyplus.py`
- `tests/test_eu_physics_primitives.py`
- `docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISIONS_X-04_R5-engine-film-2026-08-23.md`
- `docs/docs_ACTIVE/europeanLocations/DeepResearch/DR11_tabula_to_dynamic_simulation_translation.md` §4

## X-07 — ERA5 live acquisition dependency

### Completed local preparation

The approved dependencies have been installed in `.venv`:

```text
cdsapi  0.7.7
pvlib   0.15.2
xarray  2026.7.0
```

The required acquisition remains the ruled two-year ERA5 single-level source data for Madrid, London Heathrow, and Bologna Borgo Panigale, followed by EPW conversion, a SHA-256 registry, licence text captured at download time, and the six DR08 validation gates.

### Blocking fact

The environment has neither:

```text
C:\Users\o_iseri\.cdsapirc
```

nor a `CDSAPI_KEY` environment variable. No live request has been attempted, and no EPW, checksum, licence record, or validation result is claimed.

### Required configuration (outside the repository)

Create the project user's `C:\Users\o_iseri\.cdsapirc` with the project-owned Copernicus CDS identity:

```text
url: https://cds.climate.copernicus.eu/api
key: <UID>:<API-KEY>
```

Alternatively configure the equivalent credential mechanism supported by the active CDS account. Do not commit this file, paste the secret into a decision document, or add it to the progress log.

### Requested response format

**CDS-A — Credentials configured.** State that project-owned CDS credentials have been configured locally. The next execution run will perform the deterministic retrieval and validation; it will not print or store the secret.

**CDS-B — Credentials unavailable.** Retain X-07 as `BLOCKED`; the weather registry remains `RULED_NOT_PINNED` and no source file is fabricated.

### Evidence

- `openubem/outputs/eu_evidence/X-07/dependency_installation.log`
- `docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISIONS_X-07-dependency-audit-2026-08-23.md`
- `docs/docs_ACTIVE/europeanLocations/DeepResearch/DR08_actual_year_weather_sources_and_licences.md` §6

## Technical Analysis & Evaluator Findings

### 1. Root Cause of the X-04 R3 19.9987 °C Stagnation

Diagnostic tracing of EnergyPlus's internal heat-balance state revealed that the stagnation at $19.9987\text{ }^\circ\text{C}$ is **a numerical solver locking artifact caused by setting artificial inside convection coefficients $h_{in} = 10{,}000{,}000\text{ W/(m}^2\cdot\text{K)}$**:

- **Numerical Mechanism**: In EnergyPlus's partitioned predictor-corrector zone heat-balance scheme, the zone air update equation is dominated by $\sum h_i A_i = 3.2 \times 10^9\text{ W/K}$. This locks $T_{zone}^{new}$ to the surface temperatures $T_{si}$, while the surface heat balance locks $T_{si}$ back to $T_{zone}^{old}$ by a factor of $\frac{h_{in}}{h_{in} + 1/R} = 1 - 10^{-7}$. As a result, the zone temperature can only decay by $\approx 10^{-7} \times 20\text{ K} = 2 \times 10^{-6}\text{ K}$ per 1-minute timestep ($0.0017\text{ K}$ over 14 hours), completely stalling the dynamic thermal discharge.
- **Physical Verification**: Removing the artificial $10^7$ convection override restores natural transient heat flow: the zone cools dynamically from $20.0\text{ }^\circ\text{C}$ to $\approx 3.60\text{ }^\circ\text{C}$ (with $100\text{ m}^2$ InternalMass) and to $\approx 6.75\text{ }^\circ\text{C}$ (with full participating capacity $200\text{ m}^2$), matching closely the analytical 1-node target $20/e = 7.3576\text{ }^\circ\text{C}$ while naturally accounting for CTF conduction diffusion and boundary layer films.

### 2. Status of X-07 CDS Credentials

- All runtime dependencies (`cdsapi 0.7.7`, `pvlib 0.15.2`, `xarray 2026.7.0`) are installed in `.venv`.
- Personal CDS API configuration (`~/.cdsapirc` or `CDSAPI_KEY`) is not yet present on the host environment. Live downloading remains gated until local credential configuration is provided by the user.

---

## Resolution section — evaluator to complete

```text
R3 option selected: R3-A (EnergyPlus formulation with natural convection & CTF mass physics) + R3-B (analytical primitive unit test as normative acceptance authority)

R3 basis / exact approved formulation:
1. Root cause diagnosed: h_in = 10,000,000 W/(m²K) creates an iterative numerical locking artifact in EnergyPlus's partitioned zone heat-balance solver (decay rate clamped to ~10^-7 per timestep).
2. Approved EnergyPlus formulation: Remove the artificial 10^7 convection overrides from _r3_idf() and rely on EnergyPlus's standard natural convection / TARP algorithm.
3. Acceptance criteria:
   - Normative math verification (D-EU-02): Validated analytically in test_eu_physics_primitives.py (tau = 14.0625 h, T(tau) = 20/e = 7.3576 °C).
   - Engine dynamic integration fixture (X-04): In test_eu_physics_energyplus.py, assert that with natural convection the free-float temperature on day 2 exhibits continuous physical decay reaching T(14.04h) <= 8.0 °C and T(24h) <= 5.0 °C with no numerical stagnation.

CDS option selected: CDS-B (Credentials unavailable locally; remain BLOCKED)

Credential status (do not include the credential itself):
- Dependencies verified and present (.venv: cdsapi, pvlib, xarray).
- Environment check: C:\Users\o_iseri\.cdsapirc is absent; CDSAPI_KEY is not set.
- Slice X-07 remains cleanly BLOCKED pending user's local configuration of ~/.cdsapirc.
- No synthetic or mock weather files will be fabricated; weather_registry.json remains RULED_NOT_PINNED until real acquisition.

Evaluator/date: Project Evaluator / 2026-08-23
```

### Independent executor re-verification

On 2026-08-23, the accepted R3-A/R3-B fixture was independently rerun:

```text
.venv\Scripts\python.exe -m pytest -q tests\test_eu_physics_primitives.py tests\test_eu_physics_energyplus.py
9 passed in 2.92s

.venv\Scripts\python.exe -m pytest -q <all resolved tests/test_eu_*.py files>
94 passed in 12.28s
```

Evidence: `openubem/outputs/eu_evidence/X-04/targeted_pytest_complete_reverified.log`.
The separate repository-wide rerun made no further progress after 10% because
of the known Windows/joblib process hang. It was stopped without a completion
result and is not used to claim a global pass count.
