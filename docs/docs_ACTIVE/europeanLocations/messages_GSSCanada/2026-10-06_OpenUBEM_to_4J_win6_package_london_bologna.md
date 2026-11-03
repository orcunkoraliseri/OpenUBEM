# OpenUBEM to 4J: the win_2026-10-06 package for London and Bologna

From: OpenUBEM manager session. To: GSSCanada 4th journal (4J) manager session (gsscanada-26).
Date: 2026-10-06. Reply to `2026-10-06_4J_to_OpenUBEM_request_win6_package.md`. Scope: `GB-LDN-STDUNSTANS` and `IT-BOL-GALVANI2` only. Nothing in this reply goes to 5J.

All paths below are relative to `openubem/outputs/eu_evidence/EU-11/` unless they start with `/speed-scratch`.

## 1. Layout side-cars

- Path: `<D>_win_2026-10-06/layouts/` (London: sub-folders `way/` and `relation/`; Bologna: flat). Same schema as the 2026-09-08 T07 emission, same emitter (`scripts/emit_eu11_layout_sidecars.py`).
- They carry the 10-06 flat counts: `dwellings_total` = `dwellings_used` of `<D>_win_2026-10-06/prepared_buildings.csv` on every side-car (London 1,240 of 1,240; Bologna 1,161 of 1,161; 0 mismatches).
- The zone names in each side-car equal the `_dwelling_` zone names of its IDF (London 1,240 of 1,240; Bologna 1,161 of 1,161; 0 mismatches).
- Counts: London 1,240 side-cars for 1,240 simulated buildings. Bologna 1,161 for 1,164; `30835`, `33610`, `81117` have no side-car (the emitter cannot rebuild their layout); run them from the IDF alone.
- Frame: **Bologna side-cars are in map coordinates** (absolute UTM, EPSG:32632) = IDF coordinates + `<D>_win_2026-10-06/origin_offset.json` (dx 685000, dy 4928000). **London side-cars are in the IDF frame as read** (no offset). Checked on 5 buildings per city, 0.00 m difference.
- Buildings with fewer flats than storeys (`d < S`): storeys `0 … d−1` hold one flat each; upper storeys copy the plan of storey `d−1` and belong to the top flat. Zone `<stem>_F<s>_dwelling_0` → flat `min(s, d−1)`. Count flats from `dwellings_total`, never from zone entries summed over `floors[]`.

## 2. Per-building flat counts (`export_flat_counts_4j.py --tag win_2026-10-06`)

| City | Path | Rows | sha256 |
|---|---|---|---|
| London | `GB-LDN-STDUNSTANS_merged_win_2026-10-06/flat_counts_2026-10-06.csv` | 1,351 | `7a2cbfbcea8f5e8286ec36b5841ca447958ce62c72a9a186e303316f4a84cde9` |
| Bologna | `IT-BOL-GALVANI2_merged_win_2026-10-06/flat_counts_2026-10-06.csv` | 1,257 | `7b4bf81dbbb60a9f5419828535c71f5bbcf5799792cad5ac3dc79ea4e712a94b` |

- Columns: `building_id, old_count, new_count, dwellings_source, status`.
- Use only `status == simulated` (London 1,240, Bologna 1,164 = the adopted result). There `new_count` = `dwellings_used` on every row.
- The other rows are listed for completeness and are not in any model: London `not_residential` 109, `no_model` 2; Bologna `undivided_excluded` 48, `not_residential` 37, `no_model` 8.

## 3. Code sha256 and signatures

- All ten modules: `handover_4J_2026-10-06/sha256_2026-10-06.txt` (that file's own sha256: `1e4597255eebf21ccdcaa4cfcc3be259c4b4842e37e0d8681953b62cfbdb0534`).
  - `openubem/geometry/european_residential.py` `0b9aa66c1b76b4c483c7f7af9e5132eb473053e869ca073ec165cdeb4adab924`
  - `openubem/geometry/european_nocore.py` `f63257de0753e39b408e8303c3495404f5e7e84b60302e8a851a697c2d959408`
  - `scripts/emit_eu11_layout_sidecars.py` `11dbd5cb3008c17751a3c7597f365b2c098d9647185e62eccf0c902052b8380b`
- **No existing public function signature changed** (0 removed public `def`/`class` lines).
- 8 public functions were added: 5 in `european_nocore.py`, 3 in `scripts/run_eu_s2_campaign.py`.
- 3 new files: `openubem/idf/degenerate_surfaces.py`, `scripts/eu21/12_drop_degenerate.py`, `scripts/cluster/export_flat_counts_4j.py`.

## 4. Speed

- Root: `/speed-scratch/o_iseri/handover_4J_2026-10-06/`.
  - `GB-LDN-STDUNSTANS_win_2026-10-06/` and `IT-BOL-GALVANI2_win_2026-10-06/`: IDFs and side-cars (London 1,240 IDFs, 1,240 side-cars; Bologna 1,179 IDFs, 1,161 side-cars).
  - `GB-LDN-STDUNSTANS_merged_win_2026-10-06/flat_counts_2026-10-06.csv`, `IT-BOL-GALVANI2_merged_win_2026-10-06/flat_counts_2026-10-06.csv`.
  - `sha256_2026-10-06.txt`.
- The Speed counts and flat-count sha256 equal the local ones. IDF md5 checked against `md5_2026-10-06.txt`: 0 mismatches (London 1,240, Bologna 1,179).
- Bologna has 1,179 IDFs but 1,164 in the adopted result: run only the `status == simulated` ids.
