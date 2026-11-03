# G8 — Single-family

> **Layout family:** single-family (detached, attached/rowhouse) · **Template applies:** ❌ **no corridor** —
> few zones · **Locked step:** S5 (lowest UBEM value per building, highest count in real stock).
> Backing design: `../Design_layoutgenerator.md` §5.6 (Family F), §3.1 (G8), §10 (AttachedHouse correction).

## Members (2 IDFs)

| IDF filename | OpenUBEM archetype | Family | DOE zones | Status |
|---|---|---|---|---|
| `DetachedHouse+CZ6A+IECC+2024_NBC936_Z7A_v221.idf` | DetachedHouse | single-family | handful (living / sleeping / basement / attic) | ❌ separate residential logic |
| `AttachedHouse+CZ6A+IECC+2024_NBC936_Z7A_v221.idf` | AttachedHouse | single-family (unit-in-a-row) | handful per unit | ❌ separate residential logic |

**Why grouped together:** houses — a handful of zones (living, sleeping, basement, attic/garage), **not**
corridor-packed or core/perim. **§10 correction:** AttachedHouse is **7 single-family unit triads in a row**
with party walls, **no corridor** → `single_family` (repeated), not units+corridor. README bucket for both:
`single_family_nbc936` (NBC 2020 S 9.36 Tier 1).

## Kit-of-parts / recipe — FOLLOW THE DOE STRUCTURE (user 2026-07-04, verified)

**DECISION (revisable): replicate the DOE house layout exactly.** The DOE IDFs were read (2026-07-04) and
split **vertically only** — each home has **3 zones**: `living` (the whole heated floor, one zone — **no
bedroom / living-room split**), `attic` (unheated), and `unheatedbsmt` (unheated basement). So:

- **DetachedHouse:** 3 zones — living + attic + basement. No horizontal room split (DOE has none).
- **AttachedHouse:** the same 3-zone unit **repeated per row unit** (verified: `living/attic/unheatedbsmt`
  ×7 units), shared party walls → adiabatic.

## Shape behaviour

Houses are usually compact / L; single-zone-per-floor covers most. Trivial on shape.

## Alternatives to render (A = chosen)

- **A** DOE 3-zone: living + attic + basement (chosen — matches the DOE IDF exactly).
- **B** *(not pursued)* horizontal living/sleeping split — DOE has none, so we don't invent it.

## Reference figure

Pending (S5, lowest priority). No G8 figure signed yet.

## Status caveat

No engine; likely stays per-floor unless the user wants residential room-level (open decision #5:
room-level houses vs leave detached/attached at per-floor). Lowest UBEM value per building but highest
*count* in real stock.

## Provenance

Design §3.1 (G8), §5.6 (Family F single-family), §10 (AttachedHouse = repeated single-family, no corridor),
README bucket key (`single_family_nbc936`), open decision #5 (single-family scope).
