# X-05 — S0 TABULA box-plan record

Date: 2026-08-23  
Status: `LOCAL_PASS` — deterministic plan, area-faithful saved-IDF equivalent envelope, controls integration, and a local EnergyPlus heating-only smoke test pass.

## Applied D-EU-01 inputs

For a selected archetype, the plan uses:

- plate area = `A_C_Ref / n_Storey`;
- height = `V_C / A_C_Ref`;
- exterior perimeter = `sum(A_Wall_1..3) / (n_Storey_effective_envelope * height)`;
- the two positive roots of the rectangle area/perimeter equations for length and width.

No footprint aspect ratio, orientation, or window-face allocation is invented at this stage. A negative rectangle discriminant raises `BOX_GEOMETRY_INFEASIBLE`; it never changes a TABULA area.

## Selected S0 set

| Type | Archetype |
|---|---|
| SFH | `ES.ME.SFH.04.Gen.ReEx.001.001` |
| TH | `FR.N.TH.09.Gen.ReEx.001.001` |
| MFH | `ES.ME.MFH.03.Gen.ReEx.001.001` |
| AB | `ES.ME.AB.01.Gen.ReEx.001.001` |

The S0 selection is intentionally a physically feasible four-type fixture set, not a claim that every registry row is rectangular under the ruled constraints. Exact feasibility counts are retained in `openubem/outputs/eu_evidence/X-05/geometry_feasibility.log`.

## Readback rule

`h_Transmission` is read back as the sum of the eleven cached `H_Transmission_*` workbook components divided by `A_C_Ref`. This retains TABULA's component-specific boundary factors; area-weighted U-values cannot reconstruct that target. `h_Ventilation` uses the governing direct form `0.34 * (n_use + n_inf) * h_room`.

## Evidence

`tests/test_eu_box_generator.py` together with the ES/GB/IT/FR registry tests: `60 passed in 9.25s` — `openubem/outputs/eu_evidence/X-05/targeted_pytest.log`.

## Saved-IDF equivalent-envelope resolution (2026-08-23)

TABULA separately declares floor, roof, wall, window, door, and bridge areas. The four S0 records cannot in general be converted to one closed rectangular prism while retaining every declared aggregate. The implemented adapter therefore retains the D-EU-01 rectangular-plan feasibility test and emits a clearly named **equivalent envelope** for the fixture zone: independent, non-overlapping component faces retain the authoritative areas and the zone explicitly declares `V_C` and `A_C_Ref`. It is not represented as a surveyed 3-D form.

The saved-IDF test independently reopens every S0 IDF, obtains each face area from vertices, subtracts fenestration from its parent, reads constructions and other-side coefficients, and verifies the reduced target `h_Transmission * F_red_temp` to a `1e-7 W/(m2 K)` coordinate-serialization tolerance. It also verifies the heating-only controls in the same files. The SFH fixture runs successfully in EnergyPlus 23.1 with zero severe errors.

Two engine constraints were resolved in the emitter:

- EnergyPlus prohibits windows whose parent wall has `OtherSideCoefficients`; S0 window/door hosts are exterior `b=1` walls and are emitted with the `Outdoors` boundary, which is physically equivalent for their required loss term.
- The cached calculator `H_Transmission_Floor_1` for the AB fixture differs from its display `b_Transmission_Floor_1` when evaluated as `U*b*A`. The emitter preserves the authoritative cached H term by deriving the effective b used for that component. The original display b remains in the registry unchanged for provenance.

Evidence: `openubem/outputs/eu_evidence/X-05/equivalent_envelope_and_controls_pytest.log` (`17 passed in 3.59s`) and `openubem/outputs/eu_evidence/X-05/all_european_tests_after_s0.log` (`98 passed in 13.12s`).
