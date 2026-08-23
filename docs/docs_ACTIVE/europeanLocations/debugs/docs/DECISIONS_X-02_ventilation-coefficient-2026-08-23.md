# D-X-02-02 — Ventilation coefficient identity

**Status:** RESOLVED from the pinned source workbook, 2026-08-23.

## Conflict

MVP §11.3 and §11.12 specified `0.34 * (n_air_use + n_air_infiltration) *
V_C / A_C_Ref` as the identity for `h_Ventilation`. The same document required
X-02 to copy the cached `Calc.Set.Building.h_Ventilation` values and to compare
them to `tabula_102_extra_columns_2026-08-23.csv`.

Those requirements cannot both hold. For example,
`ES.ME.AB.01.Gen.ReEx.001.001` has `n_air_use = 0.4`,
`n_air_infiltration = 0.4`, `V_C = 3376.8`, `A_C_Ref = 1238.16`, and cached
`h_Ventilation = 0.68`. The printed formula yields 0.741818..., while
`0.34 * (0.4 + 0.4) * h_room` with the source `h_room = 2.5` yields exactly
0.68.

## Ruling

Use `0.34 * (n_air_use + n_air_infiltration) * h_room` as the acceptance
identity. It reproduces all 102 direct workbook values. The registry preserves
both `V_C` and `A_C_Ref` as source geometry, but does not assert that their
ratio equals `h_room`.

## Authority and evidence

The direct source is the locally pinned `tabula-calculator.xlsx`, MD5
`c99ddc9ffcb6dc0ae7391273d9619e37`, sheet `Calc.Set.Building`; the extracted
102-row reference is `debugs/docs/tabula_102_extra_columns_2026-08-23.csv`.
The implementation test evaluates this identity on every record.
