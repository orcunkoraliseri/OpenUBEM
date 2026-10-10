# INVESTIGATION — why the four viewers still look unchanged, and why London looks empty

- **Arc**: European locations × Step 8, `EU-13B`/`EU-14B`.
- **Date**: 2026-08-30. **Trigger**: owner inspected all four regenerated viewers post-`EU-13B` `T09`/`EU-14B`
  `T05` and reported (a) no visible change versus the pre-`EU-13B` pop-ups, quoting
  `rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md`'s 95 % bar, and (b) the London viewer showing very
  few buildings.
- **Status**: both items are now root-caused and measured. Nothing in this document has been fixed; no code
  was changed. `FINDING 206` recorded below.

---

## 1. `FINDING 206` — circulation polygons are computed by the ruled partitioner but never reach the sidecar or the viewer

**Symptom.** Clicking a `DWELLING_LAYOUT_EMITTED` building (e.g. Madrid `way/388485191`) shows colored dwelling
slices with no corridor spine or stair core drawn anywhere — visually indistinguishable from the pre-`EU-13B`
pop-up the owner already rejected on 2026-08-28.

**What is correct.** The dwelling *count* and *scheme routing* are the ruled `EU-13B` output, verified against
`rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §3.1 on the same building IDs:

| building | EXAMPLE ruled zones | viewer zones-per-floor (2026-08-30 harvest) | match |
|---|---|---|---|
| `way/388485191` | 3×6 + 4×5 = 38 | `[6,6,6,5,5,5,5]` = 38 | exact |
| `way/391279229` | 4×6 + 4×5 = 44 | `[6,6,6,6,5,5,5,5]` = 44 | exact |
| `relation/3730743` | refused, 0 zones | `FALLBACK_PENDING_LAYOUT`, 0 zones | exact |
| `relation/12704090` | 6×5 = 30 | `[6,6,6,6,6]` = 30 | exact (scheme name differs, see below) |
| `way/420409335` | 2×7 + 1×6 = 20 | `[7,7,6]` = 20 | exact (scheme name differs, see below) |

Two of the five carry a scheme name (`equal_strip_multi_angle_sweep`, `l_shape_decomposition`) not listed in
the EXAMPLE doc's two named schemes (corridor slab, point block). These are legitimate additional morphology
routes in `openubem/geometry/european_residential.py` (alongside `i_shape_linear_gallery`, confirmed at
`european_residential.py:460,519,577,599`) — not a legacy leftover. The dwelling count and area partition are
correct in all five cases.

**What is missing — the actual defect.** The ruled partitioner *does* compute a real circulation polygon:

- `openubem/geometry/european_residential.py:261` — `circulation_polygon: BaseGeometry | None` field on the
  storey-layout result.
- `european_residential.py:304-306` — `circulation_polygon = _centred_circulation_region(...)`, then
  `plate_for_cutting = plate.difference(circulation_polygon)`: the corridor/stair-core shape is a real,
  non-null geometry object for every non-refused building.

But `scripts/emit_eu11_layout_sidecars.py:284-292` builds the sidecar's per-floor `zones` list by filtering the
partitioner's output to names starting with `..._dwelling_` only:

```python
for z in zones:
    if z["name"].startswith(f"{row['building_id']}_F{group.start_storey_index}_dwelling_"):
        ...
        g_zones.append({...})
```

`storey_layout.circulation_polygon` itself is never appended to `g_zones` — only its **scalar area**
(`circulation_area_m2`, line 306) is carried into the floor dict. Confirmed empirically on
`way/388485191`'s sidecar: `k['floors'][0]['zones']` holds exactly 6 objects, keys
`{name, r, z_floor, z_ceiling}`, all named `..._dwelling_N` — no corridor object anywhere, and
`k['core'] = False`.

`scripts/generate_eu_3d_viewers.py:466-519` (`drawFloorPlan`) only ever iterates `floorData.zones` — it has no
code path that could draw a circulation polygon even if the emitter supplied one; the popup's "Scheme:" badge
text (`i_shape_linear_gallery` etc.) is the only surviving evidence of the ruled scheme in the UI.

**Consequence.** Every one of the ~1,880 emitted layouts across the four districts is invisible as a *ruled*
layout in the viewer: the math changed, the picture did not. This is why the owner sees no change relative to
2026-08-28, despite `EU-13B` `T09`/`EU-14B` `T05` having genuinely resimulated all four districts.

**Not yet decided:** whether to (a) have the emitter also serialize `circulation_polygon` as a non-dwelling
zone object and have the viewer draw it (e.g. hatched, as in the EXAMPLE doc's SVGs), or (b) treat this as
cosmetic and leave it, since no `heating_kwh`/`floor_area`/`eui` depends on the polygon being drawn. Recommend
(a) — the pop-up is the owner's only inspection tool for this arc, and its entire purpose was to let the owner
see the layout.

---

## 2. The London viewer's sparseness is fully reconciled — not a bug

**Measured.** `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS/summary_prerun.json`:

```
population_attempted: 1242
population_prepared:   82
blocker_exclusions:
  MISSING_OBSERVED_EPC_AGE_BAND: 445
  UNMAPPABLE_RESIDENTIAL_TYPE:   345
  PERIOD_STRADDLE_D_GB.03_GB.04:  97
  PERIOD_STRADDLE_C_GB.02_GB.03:  77
  PERIOD_STRADDLE_B_GB.01_GB.02:  76
  PERIOD_STRADDLE_F_GB.04_GB.05:  66
  PERIOD_STRADDLE_K_GB.07_GB.08:  20
  PERIOD_STRADDLE_J_GB.06_GB.07:  19
  MISSING_OBSERVED_STOREY_COUNT:  15
```

Sum of blocker exclusions = 1,160 = 1,242 − 82, exact. The viewer draws the full EU-02 population (1,242
residential + 109 excluded = 1,351 footprints, confirmed by parsing the embedded scene JSON), of which only 82
(6.6 %) ever entered the `S2` campaign and can carry a layout. The other 93.4 % render as footprint-only
(`NOT SIMULATED` badge) by design — this is not a rendering defect, and no building count was silently
dropped.

**Why London differs so much from Madrid (80 % prepared) / Lyon (56 %) / Bologna (99 %).** The dominant
reasons are `MISSING_OBSERVED_EPC_AGE_BAND` (38.3 % of the gap) and `UNMAPPABLE_RESIDENTIAL_TYPE` (29.7 %,
already tracked under `D-EU-37`), plus six ISTAT/EPC-band-tie exclusions (30.6 % combined). None of this is
new instrumentation — `summary_prerun.json` already carried these counts before this investigation; they had
simply not been read against the viewer's building count before.

**No action taken.** `D-EU-37` (extend the typology table) already covers `UNMAPPABLE_RESIDENTIAL_TYPE`; the
`MISSING_OBSERVED_EPC_AGE_BAND` 445 has no open decision request yet and is not raised here as one — flagged
only so it is not re-discovered as a mystery next time someone opens the London viewer.

---

## 3. What was and was not touched

No code, sidecar, viewer, or manifest was changed while producing this document. All numbers above are read
from the already-harvested `2026-08-30` sidecars, viewers and `summary_prerun.json` files.

## 4. Reproduction

| artefact | path |
|---|---|
| zone-count cross-check | ad hoc, `.venv/Scripts/python.exe` parsing `<script type="application/json" id="scene">` in each viewer |
| circulation-polygon trace | `openubem/geometry/european_residential.py:261-346`, `scripts/emit_eu11_layout_sidecars.py:275-311` |
| London population reconciliation | `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS/summary_prerun.json` |
| acceptance sheet used for the zone-count cross-check | `rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §3.1, §6 |
