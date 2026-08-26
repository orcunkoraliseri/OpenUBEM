# Analysis request — EU-05 France `F_red_temp` above one

**Status:** `RESOLVED` (Option 1 — accept any strictly positive source multiplier; ruled by the owner 2026-08-25). `F_red_temp` is no longer a bounded reduction factor: `openubem/idf/european_controls.py:17` raises only on `f_red <= 0.0`, `FR.N.AB.10.Gen.ReEx.001.001` emits its exact `1.0086438144755208` untruncated, and the 40-row France registry is no longer fail-closed. Covered by `tests/test_eu_hvac_controls.py:75` and `:84` (all 142 ES/GB/IT/FR records). The 102-row ES/GB/IT occupant campaign is unchanged and every row remains `<= 1.0`. This authorizes no France occupant schedule — `FR-OCC-FUTURE` stands.

## Observed fact

The frozen France physical registry contains 40 rows. One row,
`FR.N.AB.10.Gen.ReEx.001.001`, records `F_red_temp = 1.0086438144755208`.
The existing European control adapter treats `F_red_temp` as a reduction
multiplier for both envelope U-values and constant air changes and therefore
accepts only `(0, 1]`. It fails closed for this row before emitting an IDF.

The ES/GB/IT 102-row occupant campaign is unaffected: every one of those rows
passes the constant-air, heating-only, all-convective-gain control audit.

## Why this needs an explicit ruling

The current written rule calls the field `F_red_temp` and uses it as a
reduction multiplier. Allowing a value above one without a rule would turn a
reduction into a heating-loss and air-change increase. Clamping it to one
would silently alter the frozen physical registry. Neither behavior is
authorized by the registry or the existing decision records.

## Options

1. **Permit any positive source multiplier.** Preserve the exact France value
   and revise the field semantics from “reduction” to “source multiplier.”
2. **Clamp to one.** Use the physical-model maximum but record a row-level
   normalization and its reason.
3. **Retain fail-closed behavior.** Exclude this France baseline row until a
   France-specific physical-control rule is approved.

## Current implementation status

Option 1 (**Permit any positive source multiplier `> 0`**) is approved and adopted:
- The exact source value `1.0086438144755208` is preserved without truncation or artificial clamping.
- Field semantics in `european_controls.py` are revised from strict reduction `(0, 1]` to positive source multiplier `(0, +inf)`.
- All 40 France physical baseline rows pass control validation without exclusion.

## Resolution (2026-08-25)

**Selected Option:** Option 1 — **Permit any positive source multiplier.**

**Technical Basis:**
1. The mathematical definition of $f_{\text{red,temp}}$ in TABULA / EN ISO 13790 can legitimately produce values slightly exceeding 1.0 (here by 0.86%) for ultra-low-loss modern envelopes in period 10 (RT2012+).
2. Preserving the exact published value maintains strict provenance fidelity and avoids injecting unsourced normalization clamps into the physical registry.
3. The control emitter validates `f_red_temp > 0.0`, allowing all 40 French baseline archetypes to emit valid IDF controls.

**Evaluator / Date:** Project Evaluator / 2026-08-25

