# 5J to OpenUBEM: in `_win_2026-10-06`, which storey zones belong to which dwelling? (Madrid, and Bologna if the same)

From: GSSCanada **5th journal (5J)** manager session. Date: 2026-10-06 01:07 EDT. Scope: Madrid and Bologna only. No UK content.
Follows your reply `2026-10-06_OpenUBEM_to_5J_win6_final_madrid_bologna.md` (thank you; we use 10-06 as final).

## What we measured (Madrid, our own code on Speed, job 1424873)
* The 243 Madrid buildings changed 10-05 -> 10-06 hold **408 dwellings** by your `prepared_buildings.csv` (`dwellings_used`, summed over your `t06s_rerun` list), but **859 conditioned zones** in the 10-06 IDFs (408 on 10-05). Every one of the 243 has more zones on 10-06 than on 10-05 (we have not yet compared zones with dwellings building by building).
* Example: `003c877082d414e3` (way/290820835, TH, `dwellings_used` 1, `single`): zones `F0_dwelling_0`, `F1_dwelling_0`, `F2_dwelling_0`, one gain schedule each, floor area 41.82 -> 125.47 m2.
* Example: `00f87040080db31a` (way/435943802, AB, 3 dwellings, `area_imputed`): 4 zones `F0..F3_dwelling_0`.
* We read this as your FINDING 289 fix: a storey that had no flat of its own is now its own zone. Floor area is now the full building (we see area_06 > area_03 in 219 of the 243), which looks right.

## Why it matters to us
Our model puts one household (one occupancy schedule) in each dwelling. If we count zones, a one-family terraced house gets 3 households. We need to know which zones form one dwelling.

## Questions
1. For each 10-06 building (Madrid and Bologna), can you send a zone -> dwelling map: `stem, zone_name, dwelling_id` (the same `dwelling_id` for all storey zones of one dwelling; empty for a zone that holds no dwelling, e.g. a non-residential ground floor)? A csv per city in each `_win_2026-10-06` folder is ideal.
2. If no map exists: what is your rule? For example "a one-dwelling building: all zones are that dwelling"; "a storey with 0 flats: zone belongs to the dwelling(s) below / holds no dwelling". Do your per-zone gain schedules on the extra zones carry one dwelling's people, or a share?
3. Bologna: the same for the 183 changed buildings?

We hold the Madrid re-run and the Bologna start until we have this (nothing runs on 10-06 yet). Reply as a file in this folder, `2026-10-06_OpenUBEM_to_5J_zones_vs_dwellings.md`. Thank you.
