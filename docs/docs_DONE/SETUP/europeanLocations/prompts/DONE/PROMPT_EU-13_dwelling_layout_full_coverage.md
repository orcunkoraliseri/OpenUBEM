# `EU-13` — Executor prompt: extend dwelling-layout coverage from 51/4,186 to (near-)full coverage

- **Arc**: European locations × Step 8.
- **Order**: runs **after** `PROMPT_EU-12_dwelling_layout_popup.md` (already executed — side-cars,
  `layout_json` manifest column, and the pop-up all exist today). Extend that machinery; do not rebuild it.
- **Ruling**: `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-33_dwelling_layout_full_coverage_2026-08-28.md`
  — read it first, it is the spec for this task.
- **Executor**: external. **Paste everything below the rule into the tool.**
- **Date of prompt**: 2026-08-28.

---

## Task (paste from here)

You are extending the dwelling-layout coverage of the OpenUBEM European campaign
(`C:\Users\o_iseri\Desktop\OpenUBEM`). Python is **`.venv/Scripts/python.exe`** — never bare `python`. Git is
handled externally: **never commit and never stage.**

### 0. Where things stand, measured (`openubem/outputs/eu_evidence/EU-12/RESULTS_EU-12.md`)

Of 4,186 residential buildings, 1,340 are simulated and only **51** (all Madrid) carry a drawn dwelling
subdivision. The rest split as: `NON_CONVEX_TOPOLOGY_UNSUPPORTED` 609, `NARROW_FOOTPRINT_LT_8M` 183,
`COURTYARD_TOPOLOGY_UNSUPPORTED` 115, `MISSING_OBSERVED_DWELLING_COUNT` 382 (Lyon 297 + London 82 + Madrid
3). Additionally, **all 51 "successes" only extrude storey 0** (`FINDING EU-12-01`) — even the working case
is not full-height.

`D-EU-33` rules three fixes mandatory and one carried as-is. Implement in this order.

### 1. Fix `FINDING EU-12-01` — stack the partition across every storey

`openubem/geometry/european_residential.py:452` `generate_european_dwelling_layout` and `:555`
`european_layout_to_zone_specs` currently call the partition once at `floor_index=0`. Change the caller so
that for every `DWELLING_LAYOUT_EMITTED` building, the same in-plane dwelling partition is repeated at each
storey (`z_floor_m = storey_index * floor_to_floor_m`), producing `n_storey` entries in `floors[]`, each with
its own `zones[]` at the correct `z_floor`/`z_ceiling`. Do not re-run the partition geometry per floor — the
in-plane polygons are identical across storeys; only the z-offset changes. Update the IDF-building code path
identically, so the emitted zones (not just the side-car) reflect every storey. Re-run the 51 Madrid
buildings currently `DWELLING_LAYOUT_EMITTED` and confirm each side-car's `floors` array length now equals
its `storeys` field.

### 2. Extend the partition to non-convex and courtyard footprints (724 Madrid buildings)

`equal_strip_long_axis` (same file) only cuts convex, hole-free polygons. Implement a general partition that
handles both cases — for example, decompose the footprint into convex sub-polygons first (any correct
polygon-decomposition method), then apply the existing strip-partition logic within each convex piece, or an
equivalent method you can justify. Requirements, non-negotiable:

- Must pass the **existing** `audit_european_floor_partition` checks unchanged: area-error fraction at the
  current tolerance, no zone overlap or gap versus the source footprint, ≥2.5 m facade contact per dwelling.
  **Do not loosen the audit to make more buildings pass** — a building that cannot pass stays a documented
  fallback, individually named, not silently counted as `NON_CONVEX_TOPOLOGY_UNSUPPORTED` in bulk once you've
  built the general method (if it still fails after the general method, that is new information, and the
  building must be named in `RESULTS_EU-13.md`, not folded into the old bulk count).
- Re-run `allocate_european_dwellings` + the new partition for all 609 + 115 = 724 previously-unsupported
  Madrid buildings that have an observed dwelling count. Report exactly how many now emit vs how many still
  fail, and why, per building where the count of remaining failures is under 20; as a reason-census table
  above that.

### 3. Impute missing dwelling counts (382 buildings — Lyon 297, London 82, Madrid 3)

Use the existing four-tier imputation cascade (fusion → spatial → opt-in ML → statistical;
`docs/docs_ACTIVE/europeanLocations/previous/MVP_european_locations.md` Figure 2 / §3's implementation) to
derive a dwelling count for these buildings from whatever tier succeeds. Tag the result
`IMPUTED_DWELLING_COUNT` with the tier and source recorded in the side-car (new field
`dwelling_count_provenance`). Feed the imputed count into steps 1–2's partition exactly as an observed count
would be, but the `geometry_outcome` for these buildings must read
`DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`, never plain `DWELLING_LAYOUT_EMITTED` — the pop-up and the manifest
must both show this distinction, not just the side-car.

### 4. `NARROW_FOOTPRINT_LT_8M` (183 Madrid) — do not touch

Per `D-EU-33` §3.4, this stays a massing box (already floor-divided, one zone per floor). Do not relax the
8 m / 2.5 m facade-contact audit. If fewer than 183 remain after steps 1–3 shift some buildings' topology
classification, report the new count; do not otherwise act on this group.

### 5. Update the pop-up

- Add the storey selector for buildings whose `floors[]` now has more than one entry (most of the newly-fixed
  51, and all newly-emitted buildings with `storeys > 1`).
- Distinguish `DWELLING_LAYOUT_EMITTED` from `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` visibly in the header
  line (e.g. an "imputed dwelling count" badge), not just in the underlying JSON.
- Keep every rule from `PROMPT_EU-12_dwelling_layout_popup.md` §4 in force (self-contained/offline, nothing
  interpolated or beautified, coverage stated not implied, existing channels intact, no S0/S2 comparison).

### 6. Deliverable

1. Regenerated side-cars for all districts reflecting steps 1–3, plus the new `dwelling_count_provenance`
   field and the new `geometry_outcome` value.
2. Regenerated four viewers + data folders in `openubem/outputs/3D/` **and** the byte-identical mirror in
   `docs/docs_ACTIVE/europeanLocations/outputs_3D/`.
3. `RESULTS_EU-13.md` in `openubem/outputs/eu_evidence/EU-13/`: before/after coverage census per district
   (observed-emitted / imputed-emitted / narrow-fallback / any-still-failing-named), the storey-stacking fix
   confirmed on the original 51, and the partition-algorithm method chosen with its audit pass rate.
4. One appended row in `docs/docs_ACTIVE/europeanLocations/content/walkthrough_progress_log.csv`.
5. An update to `OpenUBEM_fundamentals.md` §8.5 describing the storey-stacking fix, the new partition method,
   and the imputed-count tag.
6. Any error you hit and solve: one entry in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, house
   format, before you close the task.

### 7. Do not

- Do not edit root `main.py`, any OVERVIEW or DESIGN doc, `previous/MVP_european_locations.md`, or
  `previous/WALKTHROUGH_european_locations.md`; do not annotate MVP Table 9.7.
- Do not write into `openubem/outputs/eu_certified_rerun_2026-08-28/` — read-only.
- Do not put `.py` files under `docs/`. All `.png` and figure outputs go to `openubem/outputs/`, flat.
- Do not loosen `audit_european_floor_partition`'s tolerances to inflate the coverage count.
- Do not touch `NARROW_FOOTPRINT_LT_8M` buildings beyond re-classifying them if steps 1–3 change their count.
- Do not change any archetype assignment, weather binding, or anything outside geometry/zoning and the
  viewer's presentation of it.
