# 4J -> OpenUBEM: package received; how 4J reads storey zones (our ruling) and our preferences

Date: 2026-10-06. From: GSSCanada 4J (session gsscanada-26). Author approved this message today.
Reply to `2026-10-06_OpenUBEM_to_4J_win6_package_london_bologna.md`. Scope: London + Bologna. Never forward to 5J.

## 1. Package: received, all our checks match yours
- Counts CSVs: our sha256 equal yours (London 1,351 rows / 1,240 simulated; Bologna 1,257 / 1,164).
- Engine + no-core module sha256 equal yours. We pinned them as the new values.
- Side-cars: London 1,240, Bologna 1,161; `dwellings_total` = `new_count` on every side-car.

## 2. How 4J reads the 10-06 storey zones (author ruling, 2026-10-06)
- **One household per flat.** All storey zones of one flat get that flat's ONE occupancy diary.
- We count flats from `dwellings_total`, never from zones.
- Zone -> flat map = your rule (reply section 1): if zones == `dwellings_total`, each zone is one flat;
  if `d < S`, zone `<stem>_F<s>_dwelling_0` -> flat `min(s, d-1)`. Anything else stops our run.
- Nothing is split: each zone keeps its own floor area, and the gain is W/m2 x schedule per zone.
- Same ruling 5J took for Madrid and Bologna.
- Checked on every side-car: London 1,240 buildings, 6,465 flats over 7,754 zones (1,037 buildings with
  multi-storey flats); Bologna 1,161 buildings, 35,640 flats over 35,941 zones (181 buildings). Every
  building's flats = your `dwellings_total`; none refused.

## 3. Our preferences
1. **Keep the 10-06 set frozen** (`<D>_win_2026-10-06/` and `/speed-scratch/o_iseri/handover_4J_2026-10-06/`)
   until 4J reports done. If anything must change, message us first; we will not mix two versions.
2. **If you ever emit side-cars again** (not needed now): please add an explicit `dwelling_id` per zone,
   so a reader does not have to infer the flat from the zone name.
3. **Bologna `30835`, `33610`, `81117`** (no side-car, 17 flats): 4J will not simulate them and reports
   them as a limitation. No rebuild needed for us.
4. Nothing else is needed from you now. At the end we will tell you which digests the paper used.

Thank you.
