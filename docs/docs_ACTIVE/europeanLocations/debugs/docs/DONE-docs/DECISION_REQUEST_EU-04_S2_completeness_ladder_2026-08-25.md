# Decision request — EU-04 S2 completeness ladder

**Date:** 2026-08-25  
**Status:** `RULED (C1A 31-row correction selected)`  
**Scope:** Forming the EU-04 S2 observed-building sample after the completed G1/V1 geometry remedies. This request changes no source manifest, geometry contract, or simulation input.

## Measured constraint

The original S2 rule requires two rows in every `type × age × mapping-input completeness` cell: 32 rows across four types, old/new construction bands, and high/low completeness. The retained 4,186-row corpus has 297 typed-and-dated, mapping-ready rows, but no complete low-completeness cells. Only one typed-and-dated low/incomplete row exists (`AB | OLD_PRE_1945`), so the missing cells cannot be filled by relabelling records.

Even after removing completeness as a selection dimension, the strict two-per-`type × age` rule is not formable: new-era `SFH` has one eligible row. The available mapping-ready counts are AB 146 (120 old, 26 new), MFH 123 (109 old, 14 new), TH 21 (17 old, 4 new), and SFH 7 (6 old, 1 new).

The post-remedy geometry census is a separate outcome: 28 layouts emit and 269 rows fail closed (200 non-convex, 58 narrow, 11 courtyard). It must not be a selection criterion.

Evidence:

- `openubem/outputs/eu_evidence/EU-04/s2_scope_measurement.csv`
- `openubem/outputs/eu_evidence/EU-04/s2_scope_summary.json`
- `openubem/outputs/eu_evidence/EU-04/s2_geometry_limits_diagnostic_summary.json`

## Decision

### D-EU-04-S2-C — revised S2 completeness ladder

Choose one:

- **C1 — deterministic high-completeness operational ladder (recommended):** retain S2's 32 observed buildings and select only mapping-ready rows, ordered by `building_id`, without inspecting layout or EnergyPlus outcomes. Select eight rows per type. Within each type, select four old and four new rows when each age band has at least four candidates; where this is impossible, retain the available band and fill the remainder from the other band. Under the current corpus, SFH is therefore exactly one new and seven old; AB, MFH, and TH are four old/four new. Record every selected row's completeness as `HIGH_MAPPING_INPUT_COMPLETENESS`; retain the low/incomplete population only as a census finding, not as a simulation stratum. Geometry status and fallback reason remain independent reported outcome columns. S2 must be described as a *high-completeness operational sample*, not a completeness comparison.
- **C2 — preserve the original completeness experiment:** do not form S2 until source acquisition or reconciliation supplies genuinely incomplete but typed-and-dated rows for every required low-completeness cell. No relabelling is allowed.
- **C3 — retain the original rule and defer S2:** make no selection or further implementation change.

**Owner answer:** `D-EU-04-S2-C = C1 (deterministic high-completeness operational ladder)`

## Execution boundary

No S2 sample, short-period simulation, threshold relaxation, source-manifest rewrite, or outcome-based selection is authorized until this ruling is filled. If C1 is selected, the next bounded slice must write the deterministic 32-row manifest, prove the stipulated 8-per-type/age allocation, and retain separate mapping-completeness and geometry-result columns before attempting any simulation.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-25

## Execution checkpoint — STOP (2026-08-25T20:53:42Z)

The ruled C1 preflight was implemented against the retained census and stopped
fail-closed before writing a sample manifest. The corpus has **seven**, not
eight, mapping-ready SFH rows: six `OLD_PRE_1945` and one `NEW_POST_1945`.
Therefore the stated 8-per-type, 32-row C1 quota is mathematically impossible
without adding an incomplete row, duplicating a building, or changing another
type quota. None of those substitutions is authorized by C1.

`pytest -q tests/test_eu_s2_c1_sample.py tests/test_eu_s2_geometry_remedies.py tests/test_eu_floor_partition_audit.py` passes 21 tests. The C1 preflight test pins the source fact and requires the attempted 32-row selector to refuse it. No S2 sample, source-manifest change, or simulation was created.

**Required correction:** record an amended owner decision that either (a)
defines a 31-row high-completeness operational sample with seven SFH rows, or
(b) changes the type quotas by an explicit, non-outcome-based rule. Until then,
the C1 selection remains `STOPPED_NOT_FORMABLE`.

## Owner amendment — C1A accepted (2026-08-25T20:56:16Z)

The owner authorized the conservative correction following the preflight:
`D-EU-04-S2-C = C1A`. S2 is a **31-row high-completeness operational sample**
with quotas `AB=8`, `MFH=8`, `TH=8`, and `SFH=7`. The SFH composition is six
old and one new, exactly matching the retained source stock. The other three
types remain four old/four new. No incomplete row, duplicate, geometry outcome,
or simulation outcome may affect selection.

The deterministic manifest is
`openubem/outputs/eu_evidence/EU-04/s2_c1_high_completeness_sample.csv`; its
summary is `s2_c1_high_completeness_sample_summary.json`. It contains the
independent geometry-result columns and must be called a high-completeness
operational sample, never a completeness comparison. This decision forms S2's
input sample only; it does not authorize the short-period simulation slice.
