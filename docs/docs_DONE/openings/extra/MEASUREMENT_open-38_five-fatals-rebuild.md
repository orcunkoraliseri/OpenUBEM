# MEASUREMENT — OPEN-38 T05: rebuilding the 5 unmeasured `LAUNDRYROOMFLR1` fatals

**Date:** 2026-08-19 · **Task:** T05 of `PLAN_ten-items-2026-08-19.md`

## 0. Pre-registered prediction (written before any build/sim ran)

> All 5 unmeasured buildings, rebuilt in `layout_assign` mode from a frozen `01_buildings.gpkg`,
> will classify as `SmallHotel` (matching all 7 of T04's already-established population) and will
> reproduce the `CalcHeatBalanceInsideSurf` Severe in zone `LAUNDRYROOMFLR1`, Sizing phase, immediate
> two-space `**  Fatal  **`, `n_severe=1` — the same mechanism as the 2 already-measured buildings,
> not necessarily the same temperature (the runaway is a numerical divergence and small input drift
> between the fixture used here and the original E02 corpus is expected to move the exact value).
>
> **Fixture choice, decided before running, not after seeing a result:** the
> `docs/docs_VALIDATION/.../phaseE/<cell>/01_buildings.gpkg` fixture (dated 2026-06-28) was **not**
> used, because it was already tried once, independently, on 2026-08-18
> (`scratchpad/e-la-20-investigation/i03/part1_passers.py`) for `way/965718402` and `way/965718403`
> under this same real pipeline, and it did **not** reproduce the known fatal (`way/965718402`
> completed successfully, 0 Severe; `way/965718403` crashed abnormally, exit `-1`, no `eplusout.end`
> at all — see `part1_results.csv`). That fixture is 43 days older than the 2026-08-10 harvest that
> produced the original `.err` files. Instead this task uses
> `%LOCALAPPDATA%/Temp/ubem_validation/open48_refleet/<cell>/01_buildings.gpkg`, dated **2026-08-12,
> only 2 days after** the harvest — the closest-in-time frozen corpus on disk. Prediction: this
> fixture reproduces the mechanism where the older one did not, because it is closer to whatever OSM
> state produced the harvest.
>
> **Positive control (hard rule 9):** `way/965718402` is rebuilt again, independently, as this task's
> own positive control. If it does not reproduce, the other five results below are void.

**Both predictions held.** All 6 (5 unmeasured + positive control) reproduced the mechanism. See §2.

## 1. The blocker was stale — evidence, not assertion

The register's stated blocker ("no IDF survives for them") is true of the **original E02 IDF corpus**
(`ubem_e02_fleet\<cell>\step3_layout_assign\idfs\`), confirmed still gone: `ubem_e02_harvest` — the
surviving `.err`/`.eio`/`.end`/`.sql` harvest that the 2026-08-17 sweep left behind — was re-checked
directly for all 7 target directories and **none carry an `.idf` file**, only the four non-IDF
artifacts. That part of the blocker is real. It is **not** a capability statement: the pipeline can
build a fresh `layout_assign` IDF for any of these osm_ids from a current `01_buildings.gpkg`, and
this task did so for all 5 unmeasured + 1 positive control.

## 2. Population and result

Re-derived from `extra/MEASUREMENT_open-38_laundryroom.md`'s 7-building population (itself independently
re-derived from all 8,160 raw `layout_assign` `.err` files, not carried from the register). Two of the
7 already have a build attempt on record — `nyc_rural/way/965718402` and `nyc_rural/way/965718403`,
per the register's OPEN-07 2026-08-18 amendment (`scratchpad/e-la-20-investigation/i03/`). The 5
remaining are this task's target population.

| cell | osm_id | role | archetype (classify(), current HEAD) | original register temp (°C) |
|---|---|---|---|---|
| la_centre | way/427942886 | unmeasured | SmallHotel | −12,901.09 |
| la_urban | relation/6374725 | unmeasured | SmallHotel | −23,743.03 |
| la_urban | way/401910463 | unmeasured | SmallHotel | +182,399.27 |
| la_urban | way/428846131 | unmeasured | SmallHotel | −59,865.37 |
| nyc_rural | way/965718400 | unmeasured | SmallHotel | −12,459.96 |
| nyc_rural | way/965718402 | **positive control** | SmallHotel | −11,949.70 |

Script: `scripts/analysis/open38_five_fatals_rebuild_2026-08-19.py`. Output:
`openubem/outputs/comparisons/open38_five_fatals_rebuild.csv`. Real pipeline, unmodified:
`BuildingClassifier().classify()` → `assign_climate_zones()` → `enrich_semantics()` →
`run_step3(resolution_mode="layout_assign")` → EnergyPlus via the project's own
`openubem.simulation.runner.run_energyplus` (`-w epw -d workdir -x -r idf`, the canonical command,
`-x` present as required). Max 4 concurrent EnergyPlus processes (`ThreadPoolExecutor(max_workers=4)`).

**Result: 6/6 reproduce, exactly the same mechanism, every one:**

| cell | osm_id | role | sim result | rebuilt Severe line |
|---|---|---|---|---|
| la_centre | way/427942886 | unmeasured | `failed_fatal`, n_severe=1, `**  Fatal  **` | `CalcHeatBalanceInsideSurf: The temperature of -13427.15 C for zone="LAUNDRYROOMFLR1", for surface="P_LAUNDRYROOMFLR1_4_0_0"` |
| la_urban | relation/6374725 | unmeasured | `failed_fatal`, n_severe=1, `**  Fatal  **` | `... -16027.29 C for zone="LAUNDRYROOMFLR1", for surface="W_LAUNDRYROOMFLR1_3_0_0"` |
| la_urban | way/401910463 | unmeasured | `failed_fatal`, n_severe=1, `**  Fatal  **` | `... 354143.11 C for zone="LAUNDRYROOMFLR1", for surface="P_LAUNDRYROOMFLR1_10010_0_10008"` |
| la_urban | way/428846131 | unmeasured | `failed_fatal`, n_severe=1, `**  Fatal  **` | `... -130384.15 C for zone="LAUNDRYROOMFLR1", for surface="P_LAUNDRYROOMFLR1_4_0_0"` |
| nyc_rural | way/965718400 | unmeasured | `failed_fatal`, n_severe=1, `**  Fatal  **` | `... 63653.38 C for zone="LAUNDRYROOMFLR1", for surface="P_LAUNDRYROOMFLR1_10010_0_10008"` |
| nyc_rural | way/965718402 | **positive control** | `failed_fatal`, n_severe=1, `**  Fatal  **` | `... -12646.35 C for zone="LAUNDRYROOMFLR1", for surface="W_LAUNDRYROOMFLR1_3_0_0"` |

Every one of the 6: `CalcHeatBalanceInsideSurf`, zone `LAUNDRYROOMFLR1`, **0 Severe in Warmup / 1 in
Sizing** (Sizing phase, matching T04/OPEN-07's established framing, not Warmup), immediate fatal on
the first Severe, genuine two-space `**  Fatal  **` grepped directly (hard rule 3; `fatal_two_space`
column in the CSV, all `True`). `la_urban/way_401910463`'s rebuilt surface name,
`P_LAUNDRYROOMFLR1_10010_0_10008`, is **byte-identical** to the surface name the register's own
2026-08-06 director-verified read cites for this exact building.

**Temperature values are not bit-identical to the original harvest** (expected — the fixture used
here is dated 2 days after the harvest, not the harvest's own now-deleted input) and one
(`way/965718400`: original −12,459.96, rebuilt +63,653.38) even flips sign. This is not read as
non-reproduction: `CalcHeatBalanceInsideSurf` divergence is a numerical runaway (the 7 originally
recorded values already span 5 orders of magnitude, −59,865 to +182,399 °C, so extreme sensitivity to
tiny input perturbation is the established character of this failure, not new here). **What "reproduces
the known signature" is measured against — the EnergyPlus check, the zone, the phase, the severity
count, the marker form — matches on 6/6, every dimension, every building.** The positive control passed;
per hard rule 9, the other 5 results stand.

## 3. Mode, named explicitly (binding context item 2)

All 6 builds ran under `resolution_mode="layout_assign"` explicitly, the same mode the original 7
fatals were raised under and the same mode T04's population was scanned in. No auto/layout_assign
mismatch of the kind that hollowed out 3 of T08's defects applies here — this task's corpus and its
target population's mode agree.

## 4. Negative controls — a healthy `layout_assign` sibling per cell completes

One healthy `layout_assign` sibling per cell was picked from the surviving E02 harvest's own `.end`
files (0 Severe, fast runtime, confirmed healthy in the original 2026-08-10 harvest before rebuilding):

| cell | osm_id | archetype in E02 harvest / current classify() | rebuild result |
|---|---|---|---|
| la_centre | relation/6333145 | (23 Warning; 0 Severe in harvest) / **Courthouse** now | `success`, 0 Severe |
| la_urban | relation/6356887 | (169,550 Warning; 0 Severe in harvest) / **SmallOffice** now | `success`, 0 Severe |
| nyc_rural | way/1103897842 | (21 Warning; 0 Severe in harvest) / **OpenUBEMUnknown** now | `success`, 0 Severe |

All 3 completed cleanly under current HEAD, in the same cells, same mode, same rebuild pipeline as the
6 fatals above. **Caveat, disclosed:** none of the 3 classify as `SmallHotel` today (a classifier-drift
finding of the same shape already documented elsewhere for OPEN-06/OPEN-07 — not new here, not
re-investigated by this task) — so this negative control is matched on cell+mode, not on archetype.
The register's own already-existing, separate finding is the stronger archetype-matched control: **of
41 `SmallHotel`-substituted `layout_assign` buildings (T04/OPEN-07's population), only 7 fail — the
other 34 complete** — so `SmallHotel` substitution alone is known, independently of this task, to be
necessary but not sufficient. This task adds: healthy `layout_assign` runs of any archetype, in these
same 3 cells, under current HEAD, complete without incident — the fatal is not a mode-wide or
cell-wide phenomenon.

## 5. New capability this task unlocks: the subsurface-fit question, settled

T04 (2026-08-18) found OPEN-38's second open question — "do unfitted subsurfaces occur below the
CHKSBS warning threshold, on the dying zone specifically?" — **not determinable from `.err`**, because
no IDF geometry existed on disk to check directly. It now does, for 6 of the 7 fatals. Reusing OPEN-07's
own subsurface-fit test (`test_subsurface_fit`/`run_subsurface_census`,
`scripts/analysis/open07_smallhotel_idf_diff.py`), gated by the same healthy-prototype control already
established there:

```
control (SmallHotel_90.1-2013.idf): 106 subsurfaces, 106 fitted, 0 unfitted   [gate: non-vacuity]
```

All 6 rebuilt fatal IDFs: **106/106 fitted, 0 unfitted — identical to the control.** Each carries
exactly 3 subsurfaces on `LAUNDRYROOMFLR1`'s own base surfaces (`W_LaundryRoomFlr1_3_0_0`, all
`Window` type); **all 3 are fitted on every one of the 6 buildings** (`max_plane_dist=0.0000`,
`all_vertices_inside_2d=True`). Each rebuilt `.err` also carries exactly **3** `"Base surface does not
surround subsurface"` (CHKSBS) warnings — matching T04's original census count exactly, 3/3, on all 6 —
consistent with T04's finding that those 3 named warnings sit on `RearStairs`/`Corridor`/`FrontStairs`,
not on `LaundryRoomFlr1`.

**This settles the question T04 could only leave open:** unfitted subsurfaces, checked directly against
real IDF geometry rather than inferred from `.err` alone, are **not present on the dying zone, on any of
the 6 buildings measured.** T04's "refuted on the dying zone" conclusion (drawn from indirect evidence)
is now confirmed directly. Script:
`scripts/analysis/open38_five_fatals_subsurface_check_2026-08-19.py` (read-only, reuses OPEN-07's own
tested functions, no new geometry code written).

## 6. Empty-output-directory check (hard rule 7)

All 9 run directories (6 fatal + 3 healthy) were checked for emptiness after simulation.
**None were empty** — `empty_dir_serial_reverify` is `False` for all 9 rows in the CSV. No
false-failure risk from the 4-worker concurrency cap in this run.

## 7. What this does and does not settle

**Settled:** the register's "no IDF survives, cannot measure" blocker was stale as a capability claim.
All 5 previously-unmeasured `LAUNDRYROOMFLR1` fatals reproduce the identical mechanism as the 2
already-measured ones and as each other — same EnergyPlus check, same zone, same phase, same severity
count, genuine two-space fatal. The positive control passed. The subsurface-fit sub-question, open since
T04, is now answered directly: not the mechanism, confirmed on real geometry, 6/6.

**Not settled, and not claimed to be:** *why* `LaundryRoomFlr1` specifically runs away when the
`SmallHotel` prototype is substituted via `layout_assign` — OPEN-38's original first open question.
This task does not open the substituted-prototype's construction/schedule assignment, HVAC sizing
inputs, or scaling factor to look for the actual driving cause; it only establishes that the failure
is real, reproducible, mode-consistent, and not a subsurface-geometry artifact. **Do not merge OPEN-38
into OPEN-42** — nothing measured here touches the five-axis distinction the director already ruled on
2026-08-18; this task found no evidence against that ruling.

## Artifacts

- `scripts/analysis/open38_five_fatals_rebuild_2026-08-19.py`
- `scripts/analysis/open38_five_fatals_subsurface_check_2026-08-19.py`
- `openubem/outputs/comparisons/open38_five_fatals_rebuild.csv`
- Full rebuilt IDFs and EnergyPlus outputs: `scratchpad/open38-t05-rebuild/<cell>/step3_layout_assign/idfs/`
  and `scratchpad/open38-t05-rebuild/<cell>/sim/<stem>/` (9 buildings total: 6 fatal + 3 healthy)
