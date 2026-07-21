# G7 — Multi-tenant strip

> **Layout family:** strip / tenant-slice · **Template applies:** ❌ **no shared corridor** — linear tenant
> slicing · **Locked step:** S5 (low priority). Backing design:
> `../Design_layoutgenerator.md` §5.5 (Family E — stripmall), §3.1 (G7).

## Members (1 IDF)

| IDF filename | OpenUBEM archetype | Family | DOE zones | Status |
|---|---|---|---|---|
| `ASHRAE901_RetailStripmall_STD2022_Buffalo_NECB17_Z7A_v221.idf` | RetailStripmall | strip / tenant-slice | 10 tenant boxes (2 anchor + 8 inline) | ❌ single-zone today |

**Why its own group:** a strip mall is a **row of independent tenant boxes**, each with its own exterior
access — **no shared corridor**, no core. Neither the corridor template (G1/G2/G3/G6) nor a single open
volume (G5) fits; it needs its own linear tenant slicer. Floorplate is a rectangular bar (§10).

## Kit-of-parts (zero-fitted)

DOE layout = **2 anchor tenants + 8 inline tenants = 10** independent single zones along the major axis
(Deru 2011). Each tenant is one zone with its own facade access; party walls between tenants are adiabatic.

## Recipe + shape behaviour

Slice the footprint into **N tenant zones along the major axis** (assume a linear bar). Each tenant = one
independent single zone. Trivial on shape (bar assumption); irregular → single zone.

## Alternatives to render (A = DOE default)

- **A** N tenant boxes (DOE 2 anchor + 8 inline).
- **B** single zone.

## Reference figure

Pending (S5, low priority). No G7 figure signed yet.

## Status caveat

A simple linear slicer, low priority and low geometric risk.

## Provenance

Design §3.1 (G7), §5.5 (Family E stripmall = linear tenant slice), §10 (rectangular bar floorplate).
