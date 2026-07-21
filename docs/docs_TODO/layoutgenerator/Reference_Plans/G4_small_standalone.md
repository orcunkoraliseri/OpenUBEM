# G4 — Small standalone

> **Layout family:** single / functional-split · **Template applies:** ❌ **no corridor** — single or 2-part ·
> **Locked step:** SmallOffice at S3 (its own call), the rest at S5.
> Backing design: `../Design_layoutgenerator.md` §5.4 (Family D functional-split), §5.5 (Family E single),
> groups §3.1 (G4). **No corridor, no packed rooms** — forcing a corridor here is wrong.

## Members (5 IDFs)

| IDF filename | OpenUBEM archetype | Family | DOE zones | Status |
|---|---|---|---|---|
| `ASHRAE901_OfficeSmall_STD2022_Buffalo_NECB17_Z7A_v221.idf` | SmallOffice | core+perimeter (compact) | **6** total · 5/floor (4 perim + core) | ⚠️ compact via geomeppy; non-rect degrades |
| `ASHRAE901_RetailStandalone_STD2022_Buffalo_NECB17_Z7A_v221.idf` | RetailStandalone | functional-split | 2 (Sales 80% + Storage 20%) | ❌ single-zone today |
| `MT5_HPE_NV_ECW_LED Small_Retail_NECB17_Z7A_v221.idf` | SmallRetail | functional-split / single | 1–2 | ❌ single-zone today |
| `ASHRAE901_RestaurantFastFood_STD2022_Buffalo_NECB17_Z7A_v221.idf` | QuickServiceRestaurant | functional-split | 2 (Dining + Kitchen) | ❌ single-zone today |
| `ASHRAE901_RestaurantSitDown_STD2022_Buffalo_NECB17_Z7A_v221.idf` | FullServiceRestaurant | functional-split | 2 (Dining + Kitchen) | ❌ single-zone today |

**Why grouped together:** small footprints with **no shared corridor** — either one open zone or a simple
front/back functional split (sales·dining vs kitchen·storage). Restaurants especially have **no corridor
and no room separation** — this group is exactly where the corridor template must NOT be forced.

## SmallOffice placement — RESOLVED: stands alone (user 2026-07-04)

**DECISION (revisable):** SmallOffice gets its **own core/perim alternative**, not lumped with the
restaurant/retail functional-split. It is a genuine 5-zone core+perimeter building (like G3), so it zones
via core/perim on a compact footprint. It stays a G4 *member* only by scale; its layout follows the
office (Family B) logic, separate from the front/back retail split. (User: "up to you… if it does not fit
with restaurants there could be another alternative"; manager chose stand-alone.)

## Kit-of-parts (zero-fitted area fractions, L09)

| Archetype | functional zones (area fraction) | source |
|---|---|---|
| RetailStandalone | Sales 80% + Storage/Support 20% (rear) | Deru 2011 §3.1.8 |
| RestaurantFastFood / SitDown | Dining + Kitchen | Deru 2011 §3.1 |
| SmallOffice | 4 perimeter (4.57 m App-G) + core residual | ASHRAE 90.1 App-G / L09 |

## Recipe + shape behaviour

- **Functional-split (retail, restaurants):** slice the footprint transversely along its major axis into
  bands sized by area fractions (public/sales/dining band on the entrance side, storage/kitchen at rear).
  No corridor, no buffer, single storey. On L/U shapes place the dominant band in the largest wing;
  irregular/small → single zone.
- **SmallOffice:** core+perimeter (Family B) on compact; degrade non-rect.

## Alternatives to render (A = default)

- **A** single open zone.
- **B** functional front/back split (sales·dining / kitchen·storage).
- *(SmallOffice: single core/perim box, per the placement decision above.)*

## Reference figure

Pending (S5, except SmallOffice which is decided at S3). No G4 figure signed yet.

## Status caveat

**DECISION (user 2026-07-04, revisable): BUILD the functional split** ("split of course"). The core idea of
the layout generator is to *adapt DOE standard layouts to new footprint shapes while preserving each room's
function* — so retail Sales/Storage and restaurant Dining/Kitchen are split, not left as one box.
Functional-split is **low geometric risk** (few big zones, no slivers).

## Provenance

Design §3.1 (G4), §5.4 (Family D area fractions), §5.2 (SmallOffice core/perim), open decisions #6 (slicer)
+ SmallOffice placement.
