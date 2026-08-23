# X-05 — S0 TABULA box-plan record

Date: 2026-08-23  
Status: `PARTIAL` — deterministic geometry plan and coefficient readback pass; saved-IDF emission remains for X-06.

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
