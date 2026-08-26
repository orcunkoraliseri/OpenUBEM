# D-X-01-01 — existing-state variant suffix

**Date:** 2026-08-23

## Conflict

Walkthrough §9.3.1 and MVP §11.3 stated that every kept
`Code_BuildingVariant` ends in `.001.001`. The copied parent UK table contains
valid existing-state rows such as
`GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001`.

## Authority and ruling

The parent generator is the higher-precedence source. It retains a row when
`code.endswith('.001')` (`tools/4thJ_step8_tabula.py:315`) and describes that
final segment as the existing state (lines 335–336). Therefore X-01 validates
the final `.001` suffix, together with `Number_BuildingVariant == 1`; it does
not constrain the preceding TABULA segment.

## Reversal condition

Reverse this ruling only if a revised parent generator changes its retained
existing-state predicate and regenerated source tables support that change.
