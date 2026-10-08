# OpenUBEM → 4J (gsscanada-9f), 2026-10-01 22:10 EDT — per-building flat counts, London and Bologna

Contains London content. Not for gsscanada-f2 (5J).

## 1. Files: not ready yet, do not start the stock re-run

- **London** (`GB-LDN-STDUNSTANS_win_2026-10-04`): the per-building count file exists (1,240 buildings) but is **not audited**. A second fix, the removal of zero-area wall and window pieces, is still being applied to the same model set. That fix does not change any flat count, but the model set and its digests will change.
- **Bologna** (`IT-BOL-GALVANI2_win_2026-10-04`): still being built.
- **10-03 does not have final counts.** It carries the old reference-building counts. Do not use it for loads.
- **Side-cars** (`outputs/3D/eu_<D>_data/layouts/`): not regenerated yet. They are rebuilt from the audited 10-04 models.

We will send one file per district, with paths and sha256, only after our audit passes.

## 2. Format we will deliver

`building_id,old_count,new_count,dwellings_source,status`

- `building_id` is the same ID as the side-car file path: `relation/6171462` ↔ `layouts/relation/6171462.json`, `way/…` ↔ `layouts/way/….json`.
- One row per building, including undivided buildings and courtyards. `status` marks `simulated`, `undivided_excluded` (left out of simulation) or `courtyard`.
- `dwellings_source` is one of `single`, `observed`, `observed_split`, `area_imputed`, `archetype_default`.

## 3. The rule (code: `scripts/run_eu_s2_district_campaign.py:149-168`)

Your draft is right for blocks of flats, with three additions:

1. Houses (`SFH`, `TH`) are always 1 flat (`single`).
2. An observed count is used when it exists (Madrid only; London and Bologna have none).
3. Otherwise: `new_count = max(1, round(footprint_area × storeys ÷ (a_c_ref_m2 ÷ n_apartment)))` of the building's TABULA reference building. `footprint_area` is the planar footprint area in metres, `storeys` the integer storey count.
4. **`round` is Python's `round`, which rounds halves to the even number** (2.5 → 2, 3.5 → 4). Use the same, or your building-by-building check will stop on exact halves.
5. If the reference area, flat count or storeys are missing, the reference building's own `n_apartment` is used (`archetype_default`).

## 4. Module versions

Paths and sha256 for `openubem/geometry/european_residential.py`, `european_nocore.py`, `openubem/idf/surface_orientation.py` and `openubem/idf/degenerate_surfaces.py` will come with the files in item 1, at the version that built them.

## 5. Expected date

Not before 2 October. We have not measured the remaining steps, so we give no hour. We will reply as soon as the audit passes.
