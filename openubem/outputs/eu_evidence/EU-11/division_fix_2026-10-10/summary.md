# Division fix, three cities - merge and score (2026-10-11)

Scored with `scripts/eu22/score_division.py --floors-decide` on `<SITE>_win_2026-10-10` with layouts from `<SITE>_dw_2026-10-10`.
Correctly divided = class OK + V3 (V3 = divided, wrapped flat). Left out = every other class.

| Item | Helsinki (FI-HEL-KALLIO) | Vienna (AT-VIE-RUDOLFSHEIM) | Budapest (HU-BUD-ERZSEBETVAROS) |
|---|---|---|---|
| Homes | 580 | 536 | 805 |
| Layout files (dw tree) | 580 | 536 | 805 |
| Side-car outcomes applied (Speed) | 130 | 88 | 196 |
| OK | 253 | 249 | 210 |
| V3 | 289 | 268 | 547 |
| V1 | 37 | 17 | 48 |
| V2 | 0 | 1 | 0 |
| U1 / U2 / U3 / U4 | 0/0/0/1 | 1/0/0/0 | 0/0/0/0 |
| Correctly divided (OK + V3) | 542 | 517 | 757 |
| TARGET | >= 551 | >= 509 | >= 765 |
| Target met | NO (-9) | YES (+8) | NO (-8) |
| Share correctly divided | 93.4 % | 96.5 % | 94.0 % |
| Homes left out | 38 | 19 | 48 |
| IDF_FALLBACK | 0 | 0 | 0 |
| Flats removed by k-1 (total) | 0 | 33 | 99 |
| Homes with k-1 | 0 | 11 | 43 |

Left-out homes, storeys failing a check (homes with at least one failing storey): Helsinki C10 28, C11 21, C12 3, C13 24; Vienna C6 1, C10 14, C11 12, C12 1, C13 14; Budapest C6 2, C10 35, C11 37, C12 1, C13 33.
Lists: `<SITE>_win_2026-10-10/left_out.csv`, `division_classes.csv` (same folder).

Note: Budapest first scoring gave 609 IDF_FALLBACK because the 609 kept layouts had been copied flat into `layouts/`; they were moved to `layouts/way/` and `layouts/relation/` (407 + 398 = 805, same as the 10-09 tree) and Budapest was rescored. Helsinki and Vienna: LAYOUT_SIDECAR for all homes.
