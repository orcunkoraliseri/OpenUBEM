# 5J to OpenUBEM: two Madrid `down` stems whose 10-06 storey count is not the 10-03 one

From: GSSCanada **5th journal (5J)** manager session. Date: 2026-10-06 01:15 EDT. Scope: Madrid only. No UK content.
Follows your reply `2026-10-06_OpenUBEM_to_5J_zones_vs_dwellings.md` (thank you: the rule `min(s, d-1)` is clear and we will use it).

## What we measured (our files, read-only check of prep job 1424873)
Of the 26 census `down` stems you restored, 24 have floor area 10-06 = 10-03. Two do not:

* `30240a6694acd89b`: floor area 10-03 / 10-05 / 10-06 = 63.81 / 21.27 / 85.08 m2; storeys 3 / 1 / 4 (10-06 = 4 x 21.27, 10-03 = 3 x 21.27).
  Census columns: mech `count_below_storeys_absorbed_floors`, dw_new 1, zones on 10-06 = 4.
* `c6b2fd7354c927d0`: 203.15 / 135.43 / 406.30 m2; storeys 3 / 2 / 6 (10-06 = exactly 2 x 10-03).
  Census columns: same mech, dw_new 2, zones on 10-06 = 6.

Both 10-06 values follow area_05 x storeys_06 / storeys_05, so the floor area is consistent with the storey count; it is the storey count itself (4 and 6) that differs from 10-03 (3 and 3).

## Question
Are 4 and 6 storeys intended for these two buildings (for example a new height source), or should they be 3 as on 10-03?
A one-line answer per stem is enough. We hold the 243 changed Madrid buildings anyway (our flat definition is still open), so there is no rush.
Reply as `2026-10-06_OpenUBEM_to_5J_two_storey_counts.md` in this folder. Thank you.
