# G5 — Open-volume / big-box

> **Layout family:** single / open-plan · **Template applies:** ❌ **no corridor, no rooms** — one open
> volume is *physically correct* · **Locked step:** S5. Backing design:
> `../Design_layoutgenerator.md` §5.5 (Family E single/open-plan), §5.4 (Family D optional split), §3.1 (G5).

## Members (7 IDFs)

| IDF filename | OpenUBEM archetype | Family | DOE zones | Status |
|---|---|---|---|---|
| `ASHRAE901_Warehouse_STD2022_Buffalo_NECB17_Z7A_v221.idf` | Warehouse | single / open-plan | 3 (Office + Bulk + Fine storage) | ✅ single-zone is **correct** |
| `ASHRAE901_Warehouse_STD2022_Buffalo_50pct_downscaled_NECB17_Z7A_v221.idf` | Warehouse (50% downscaled) | single / open-plan | 3 | ✅ single-zone correct |
| `ASHRAE901_DataCenterLargeHighITE_STD2019_CAN_passthrough_v221.idf` | DataCenter (Lg, High ITE) | functional-split | few (IT + support) | ❌ passthrough / single-zone |
| `ASHRAE901_DataCenterLargeLowITE_STD2019_CAN_passthrough_v221.idf` | DataCenter (Lg, Low ITE) | functional-split | few | ❌ passthrough / single-zone |
| `SmallDataCenterHighITE_90.1-2019_6A_Buffalo_CAN_passthrough_v221.idf` | DataCenter (Sm, High ITE) | functional-split | few | ❌ passthrough / single-zone |
| `SmallDataCenterLowITE_90.1-2019_6A_Buffalo_CAN_passthrough_v221.idf` | DataCenter (Sm, Low ITE) | functional-split | few | ❌ passthrough / single-zone |
| `Supermarket_NECB17_Z7A_v221.idf` | Supermarket | functional-split | 6 (Sales/Produce/Deli/Bakery/Storage/Office) | ❌ single-zone today |

**Why grouped together:** big single-volume buildings with **no corridor and no room separation** — a
warehouse, data hall, or big-box floor is one open volume physically. Data centers are NECB-exempt
byte-copy passthroughs (README bucket `datacenter_passthrough`). This group is where the corridor template
must NOT be forced — one zone (optionally a functional split) is the correct model.

## Kit-of-parts (zero-fitted, L09/L10)

| Archetype | zones (area fraction) | source |
|---|---|---|
| Warehouse | Office + BulkStorage + FineStorage (functional) | Deru 2011 §3.1.10 |
| Supermarket | Sales 55.5 / DryStorage 13.3 / Produce 11.1 / Deli 8.9 / Bakery 6.7 / Office 4.4 | Deru 2011 §3.7 |
| DataCenter | IT/server + support | passthrough |

## Recipe + shape behaviour

`one_zone_per_floor` is **physically correct** for warehouse/big-box (L10 §4). Optional functional split
(Family D transverse area-fraction bands) only if the prototype defines one — warehouse Office/Bulk/Fine,
supermarket Sales/back-of-house. Trivial on shape: single zone regardless of shape.

## Alternatives to render (A = default)

- **A** single open zone — production default, physically correct.
- **B** optional office/storage split (warehouse) · sales/back split (supermarket).

## Reference figure

Pending (S5, low priority). No G5 figure signed yet.

## Status caveat

Warehouse single-zone is **already correct** — do not "improve" it into rooms (one open volume is physical).
**Supermarket:** per the 2026-07-04 functional-split decision, **build the split** preserving room function
(Sales / Produce / Deli / Bakery / Storage / Office). Data centers stay passthrough single-zone.

## Provenance

Design §3.1 (G5), §5.5 (Family E — big-box single-zone correct), §5.4 (optional functional split),
README bucket key (`datacenter_passthrough`).
