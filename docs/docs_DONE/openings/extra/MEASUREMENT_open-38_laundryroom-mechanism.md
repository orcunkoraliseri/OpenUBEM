# MEASUREMENT — OPEN-38 T14: does the `LAUNDRYROOMFLR1` runaway mechanism still exist at HEAD?

**Date:** 2026-08-19 · **Task:** T14 of `PLAN_twenty-items-2026-08-19.md` · **No re-simulation
performed by this task** — it reads artifacts already on disk from a same-day prior task (OPEN-38
T05, `PLAN_ten-items-2026-08-19.md`) plus the 40,800-file E02 harvest. This is a code-and-artifact
question, answered by citation.

## 1. Yes — the mechanism still exists at HEAD, reconfirmed same-day

OPEN-38 T05 (`extra/MEASUREMENT_open-38_five-fatals-rebuild.md`, completed earlier the same day as
this task) rebuilt 6 of the 7 `LAUNDRYROOMFLR1` fatals through the real, unmodified pipeline
(`BuildingClassifier().classify()` → `run_step3(resolution_mode="layout_assign")` → EnergyPlus) and
all 6 reproduced the identical signature: `CalcHeatBalanceInsideSurf` Severe in zone
`LAUNDRYROOMFLR1`, Sizing phase, `n_severe=1`, immediate two-space `**  Fatal  **`. This task treats
that as the live-at-HEAD confirmation and does not re-run it a second time the same day; the "not
settled" question T05 explicitly left open — *why* the zone runs away — is this task's own ask.

## 2. Where the substitution comes from (citation)

`openubem/geometry/layout_assigner.py:31`:
```
"SmallHotel": "ASHRAE901_HotelSmall_STD2022_Buffalo.idf",
```
`ARCHETYPE_IDF_MAP` (`layout_assigner.py:23-61`) is consulted by `BaselineIDFRegistry.get_baseline_idf()`
(`:119-124`), reached from `openubem/idf/builder.py:228` (`_layout_assign_baseline_path`), whenever
`resolution_mode == "layout_assign"` and the row's `archetype_id == "SmallHotel"`. The file is a
Buffalo, NY (ASHRAE zone 6A) DOE prototype, applied unmodified regardless of the real building's
location or climate zone — the same climate-insensitivity OPEN-19 documents for LA's HVAC.

## 3. Geometry, loads, or HVAC template — which one is the runaway a property of

Inspected directly: the rebuilt IDF `scratchpad/open38-t05-rebuild/la_centre/step3_layout_assign/idfs/way_427942886.idf`
and its EnergyPlus output `scratchpad/open38-t05-rebuild/la_centre/sim/way_427942886/{eplusout.eio,eplusout.err}`.

- **Geometry: not the cause.** The zone's own `.eio` `Zone Information` line reads
  `LAUNDRYROOMFLR1,...,MinZ=0.00,MaxZ=3.35,CeilingHeight=3.35,Volume=378.63,...,FloorArea=112.93,...`
  — a **positive, geometrically plausible volume** (112.93 m² × 3.35 m ≈ 378.4 m³, matches the
  reported 378.63 m³ to within rounding). This is **not** OPEN-56's negative/10 m³-stub mechanism:
  that defect is universal to all 8,160 buildings and independent of OPEN-38 (already established,
  register OPEN-56 §-section, X03), and this reading confirms it directly for the zone that actually
  fails here rather than by inference.
- **HVAC template: absent, not wrong.** Searched the baseline prototype
  (`docs/docs_VALIDATION/step1/Level 2 DOE round-trip/00.BaselineBuildings_NUs/ASHRAE901_HotelSmall_STD2022_Buffalo.idf`)
  for every `ZoneHVAC:EquipmentConnections` object's `Zone Name` field: `LaundryRoomFlr1` is **absent**
  from all 54 entries. The zone carries **zero HVAC** in the DOE prototype by design — it is an
  unconditioned utility space, free-floating on the heat balance alone.
- **Loads: the largest absolute internal-gain density on the floor, dumped into an unconditioned
  zone.** The same `.eio` file's `Internal Gains Nominal` line for this zone shows
  `GasEquipment "Dryer Equipment 1"` at **46,286.64 W** design level (`ElectricEquipment` "Laundry
  Equipment 1" a further 3,127.34 W), against the baseline prototype's own literal
  `40,096.02805 W` (`ASHRAE901_HotelSmall_STD2022_Buffalo.idf:16515-16526`, `EquipmentLevel`
  calculation method — an absolute value, not per-area). `layout_assigner.scale_baseline_idf()`
  (`:1049-1056`, the `_ABSOLUTE_LOAD_SPECS` loop) scales this absolute field by `area_scale_ratio`
  gated on the calculation-method field, so the density is preserved by design, not distorted by
  scaling — the baseline's own load intensity for this zone is simply extreme. The zone also hosts a
  `WaterHeater:Mixed` ambient-loss target (`Ambient Temperature Zone Name = LAUNDRYROOMFLR1`,
  `eplusout.eio:34203` in the rebuild), a second heat source into the same unconditioned volume.

**Conclusion.** The runaway is a property of the **interaction between the loads and the absence of
HVAC**, not of the zone's own geometry (volume/area are consistent and unrelated to OPEN-56) and not
of a "wrong" HVAC template (there is no HVAC template at all, by prototype design). An unconditioned
zone carrying the building's single largest absolute internal-gain density (a full-size commercial
gas dryer plus a water heater's ambient losses) has nothing to cap its free-float temperature during
`CalcHeatBalanceInsideSurf`'s Sizing-phase design-day evaluation, and the calculation diverges
numerically. This is neither a pure geometry defect nor a pure HVAC-template defect; it is a loads/
conditioning-status interaction, and it is a property of the DOE prototype itself, not of anything
`layout_assigner.py` mutates.

## 4. Why zero fatals appear in the other four modes — independently re-verified

Grepped the token `LAUNDRYROOMFLR1` across all 40,800 `.err` files in the E02 harvest
(`%LOCALAPPDATA%/Temp/ubem_e02_harvest/<cell>_<mode>/*/eplusout.err`), by mode:

| mode | files mentioning `LAUNDRYROOMFLR1` |
|---|---:|
| auto | 0 |
| building | 0 |
| floor | 0 |
| fast_zone | 0 |
| layout_assign | **8** (the 7 fatals + the 1 non-fatal, `way/965718401` — see T15) |

**This settles the "why" directly, not by inference.** The zone token `LaundryRoomFlr1` is a named
zone that exists **only inside the `SmallHotel` DOE prototype file itself**
(`ASHRAE901_HotelSmall_STD2022_Buffalo.idf`). `layout_assign` is the only mode that imports a whole
prototype's own named zones verbatim (`layout_assigner.parse_baseline_zones`,
`openubem/idf/builder.py:515`); `auto`/`building`/`floor`/`fast_zone` all synthesize their own
generic zone geometry from the real footprint and never construct a zone with this name at all — so
the zone, and therefore its failure mode, simply cannot occur outside `layout_assign`.

## Artifacts

- Reused, not re-run: `scratchpad/open38-t05-rebuild/` (OPEN-38 T05, same day)
- This task's own verification: direct `grep` over the 40,800-file E02 harvest (ad hoc, no new
  script needed — command recorded in the progress log)
