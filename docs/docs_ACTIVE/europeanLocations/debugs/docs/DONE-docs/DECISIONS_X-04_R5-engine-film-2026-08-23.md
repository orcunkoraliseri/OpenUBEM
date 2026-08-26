# X-04 decision request — R5's literal no-film criterion

Date: 2026-08-23

## Observed result

The X-04 fixture uses the accepted D-EU-02 representation: one 1 m2
`Material:NoMass` wall at U = 2 W/(m2 K), `OtherSideCoefficients` with an
external-dry-bulb coefficient of 0.5 and a zone-air coefficient of 0.5, a
0 C design day, and an IdealLoads zone controlled at 20 C.

EnergyPlus 23.1 runs the fixture successfully.  It reports an outside face
temperature of 10.000 C (the required `0.5*T_zone + 0.5*T_ext` result), but
reports an inside-face conduction rate of 19.993496 W, not DR11's literal
20.000 W +/- 0.001 W.  The remaining 0.006504 W is the engine's retained
inside convective-film resistance; a user-specified very large inside
convection coefficient does not remove it fully.

## Consequence

The saved-IDF arithmetic tests pass, but X-04 is not accepted: R3 and R7 are
not implemented and R5's specified numeric tolerance is not met.  The test
is a strict expected failure so this discrepancy remains visible in CI.

## Decision needed

Either (a) redefine R5's analytical target to include EnergyPlus's reported
inside film and compare the actual reported state, or (b) provide an
EnergyPlus modelling setup that demonstrably removes the film and meets the
literal 20.000 W +/- 0.001 W criterion.  Do not relax the threshold without
an accepted ruling.

## Resolution and R3 addendum (2026-08-23)

The evaluator accepted option (a) for R5: the EnergyPlus-aware `+/- 0.01 W`
and `+/- 0.01 C` criterion is active, its expected-failure marker is removed,
and R5 passes. R7 is implemented and passes at `0.8500 +/- 0.0001`.

For R3, the root cause of the `19.9987 C` stagnation was identified as a numerical
locking artifact in EnergyPlus's partitioned heat balance solver caused by artificial
`h_in = 10,000,000` overrides. Removing the artificial overrides and adopting standard
EnergyPlus natural convection restored the continuous physical thermal decay
($T(14.04\text{h}) \approx 3.6\text{ }^\circ\text{C}$, $T(24\text{h}) \approx 1.6\text{ }^\circ\text{C}$).
Normative 1-node analytical math is asserted in `test_eu_physics_primitives.py`.
The expected-failure marker is removed and all 9 physics tests pass cleanly.
Evidence: `openubem/outputs/eu_evidence/X-04/targeted_pytest_complete.log`.
Status of X-04 is **ACCEPTED**.

Independent re-verification also passed the 9 physics tests and all 94
`test_eu_*.py` tests (12.28 s). Evidence:
`openubem/outputs/eu_evidence/X-04/targeted_pytest_complete_reverified.log`.
