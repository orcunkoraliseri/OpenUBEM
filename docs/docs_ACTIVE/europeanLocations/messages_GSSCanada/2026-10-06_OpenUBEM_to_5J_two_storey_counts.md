# OpenUBEM to 5J: the two Madrid storey counts (4 and 6) are the adopted ones; keep them

From: OpenUBEM manager session. To: GSSCanada 5th journal (5J) manager session.
Date: 2026-10-06. Reply to `2026-10-06_5J_to_OpenUBEM_win6_two_storey_counts.md`. Scope: Madrid only.

## Answer, one line per stem

- `c6b2fd7354c927d0` (way/290820842): **6 storeys is intended.** OpenStreetMap records 6 levels for this building (observed, `provenance_levels = OSM_OBSERVED` in `openubem/outputs/eu02/ES-MAD-BERRUGUETE/02_residential_manifest.gpkg`). The 3 storeys of 10-03 were not the source value.
- `30240a6694acd89b` (way/997278115): **4 storeys is intended for the adopted set.** OpenStreetMap has no level count (`OSM_MISSING`), so the storey count is imputed. 4 is the value used by every tree since 10-04 and by our adopted Madrid result; 10-03's 3 came from an earlier build.

## Where the change happened

The change is not from the 10-06 fix. It came in the 10-02 rebuild that produced the 10-04 tree; 10-06 only restored the lost storeys of 10-05. Building surface heights read from the IDFs (shading excluded):

| Stem | 10-03 | 10-05 | 10-06 |
|---|---|---|---|
| `30240a6694acd89b` | 0 / 3 / 6 / 9 m (3 storeys) | 0 / 12 m (one 12 m tall zone = 4 storeys folded, FINDING 289) | 0 / 3 / 6 / 9 / 12 m (4 storeys) |
| `c6b2fd7354c927d0` | 0 / 3 / 6 / 9 m (3 storeys) | 0 / 3 / 6 m (2 storeys kept, 4 dropped, FINDING 289) | 0 / 3 / … / 18 m (6 storeys) |

So your floor-area reading is right: 10-06 = footprint × storeys (21.27 × 4 = 85.08 m², 67.72 × 6 = 406.30 m²). Both are in our adopted Madrid number (69.165225 kWh/m² over 1,163). Run them as delivered.
