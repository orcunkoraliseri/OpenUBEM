# European locations — Debug References (arc-local error index)

> **Scope: the `docs/docs_ACTIVE/europeanLocations` arc only** — TABULA archetypes, the four district
> S2 campaigns (Madrid `ES-MAD-BERRUGUETE`, Lyon `FR-LYO-HAUTCOEURPENTES`, London `GB-LDN-STDUNSTANS`,
> Bologna `IT-BOL-GALVANI2`), the dwelling-layout scheme, context geometry, and their Speed runs.
>
> **Search this file before debugging anything in this arc. Append to it after fixing anything.**
> Opened 2026-08-31 under `D-EU-52`, modelled on
> `C:\Users\o_iseri\Desktop\idf_reader\docs_BEM_Explanation\debug_References.md`.
>
> **This does not replace `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.** That file stays the
> repo-wide index and the CLAUDE.md hard rule ("register every solved error there before closing the
> task") is unchanged. This file is the arc-scoped view: it carries the entries that are specific to the
> European pipeline in full, and routes to the repo-wide index for everything shared with the rest of
> OpenUBEM. When an entry lives in both, the repo-wide one is authoritative.
>
> Entry format, one bullet each:
> `- **<exact symptom / error string>** — <root cause>. Fix: <what changed, file:line>. *(source doc)*`
> `[OPEN]` = cause known, not fixed. Extend an existing entry rather than adding a near-duplicate.

## Chapters

1. [Footprint → dwelling layout: the box rule and its refusals](#1-footprint--dwelling-layout)
2. [Extrusion, interzone surfaces and EnergyPlus geometry fatals](#2-extrusion-interzone-surfaces-and-energyplus-geometry-fatals)
3. [The viewer vs the simulated IDF — this arc's recurring defect](#3-the-viewer-vs-the-simulated-idf)
4. [Context geometry, shading and adiabatic party walls](#4-context-geometry-shading-and-adiabatic-party-walls)
5. [Areas, denominators and EUI arithmetic](#5-areas-denominators-and-eui-arithmetic)
6. [Speed: submission, walltime, harvest, tcsh](#6-speed-submission-walltime-harvest-tcsh)
7. [Schedules, weather and file paths](#7-schedules-weather-and-file-paths)
8. [Data acquisition per country (ES / FR / GB / IT)](#8-data-acquisition-per-country)
9. [Reproducibility and certification traps](#9-reproducibility-and-certification-traps)
10. [Method traps: how these bugs got misdiagnosed](#10-method-traps)
11. [Not-a-bug: by design in this arc](#11-not-a-bug-by-design-in-this-arc)

---

## 1. Footprint → dwelling layout

All counts measured 2026-08-31 over the 2,544 side-cars in `outputs_3D/eu_*_data/layouts/`.

- **[OPEN] `fallback_reason = "L_SHAPE_DECOMPOSITION_FAILED"`, `scheme = null`, and the building is
  simulated as one undivided box per floor — 629 of 2,544 buildings (24.7 %), a quarter of every
  district** — `classify_building_morphology` routes any plate whose denoised convex-hull deficit exceeds
  3 % to the L route (`openubem/geometry/european_residential.py:453`); that route splits at the
  re-entrant corner, partitions each wing independently through the full ruled machinery, and refuses the
  **whole building** if any wing fails (`:983`). A refusal is not a fallback shape — it drops the
  building to `one_zone_per_floor`, so it loses its dwellings, its corridor and its stair core at once.
  Fix: not fixed; this is what `D-EU-50` / `EU-17` exists to relax. *(STATE_european_locations_v4.md §3
  `FINDING 212`)*
- **[OPEN] `fallback_reason = "INTERIOR_RING_COURTYARD_UNFOLD_FAILED"` — 239 buildings (9.4 %), 13.2 % of
  Bologna** — the courtyard route exists (`european_residential.py:724`, MVP §6.4 three-wing unfolding)
  and fails on real dense perimeter blocks. Note this reason string does **not** mean the route is
  missing: it was missing before `EU-15`, it is implemented now and it refuses. Fix: not fixed
  (`EU-17`). *(same)*
- **[OPEN] `fallback_reason = "NARROW_FOOTPRINT_LT_8M"` — 144 buildings, of which 135 in Bologna
  (11.2 % of that district)** — `NARROW_FOOTPRINT_THRESHOLD_M = 8.0` (`european_residential.py:1008`)
  refuses any plate whose minimum rotated width is under 8 m. Bologna's terraced stock is genuinely
  deep-and-narrow, so the gate fires structurally, not on noise. Fix: not fixed; needs a ruled
  single-aspect scheme, not a threshold change. *(same)*
- **`fallback_reason = "DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8"` — 75 buildings, 18 of them 22.0 % of
  London** — the ruled grid table stops at 8 dwellings/floor (`european_residential.py:31`, refusal at
  `:1759`) and London's declared per-floor counts reach 35. **This is the fail-closed refusal working as
  designed** (`FINDING 202`): the count is never reduced to fit. Not a defect; it is a table limit and
  needs an owner ruling, not a fix. *(STATE v4 §4 `D-EU-50` item 4)*
- **`fallback_reason = "REGULARIZATION_AREA_DELTA_GT_2PCT"` — suspected everywhere, measured on 2 of
  2,544** — `REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION = 0.02` (`european_residential.py:32`, tested at
  `:74`, refusal at `:918` and `:986`) is the obvious suspect for "the box rule", and it is almost never
  the binding gate: the morphology dispatch upstream has already routed non-box plates elsewhere.
  Diagnostic rule: read `fallback_reason` before blaming the squaring tolerance. *(STATE v4 §3
  `FINDING 212` item 1)*
- **`FALLBACK_PENDING_LAYOUT / PARTITION_AUDIT_FAILED` with
  `partition_audit.failures = ('AREA_GAP', 'OUTSIDE_FOOTPRINT')` at `area_error_fraction = 5.09e-12`** —
  the partition is exact and the audit fails on float noise: the generator rotated about the literal
  coordinate origin while the audit compared against an **absolute** `1e-8 m²` tolerance, so the noise
  scaled with distance from (0,0) and layout success became **CRS-dependent** (clean in EPSG:32631,
  failing in EPSG:2154). Fix: rotate about `footprint.centroid` (`european_residential.py:511`) and audit
  with the footprint-relative `EUROPEAN_TOPOLOGY_TOLERANCE_FRACTION`. CLOSED 2026-08-27 by re-measurement
  (297/297 agreement between projections); it also moved Lyon's emission from 18 to 28.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 5)*
- **`HABITABILITY_GATE_FAILED_AFTER_ROTATION` on ~84 % of the fleet, coverage ~16 % instead of ~97 %** —
  the equal-area bisection cuts with blade rectangles built as `box(mid, -1e6, 1e6, 1e6)`; a footprint
  left in absolute UTM coordinates has a northing near 4.9 × 10⁶ m, **outside the blade**, so every
  intersection is empty and the loop falls through to the habitability token — a misattribution, not the
  real cause. Fix: translate each footprint to its own centroid before partitioning; measured coverage
  15.76 % → 97.05 % over the same 2,544 buildings with no other change. 🔴 A reason token emitted by
  fall-through is not evidence of that failure mode — check the cell count before believing the token.
  *(rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md §8)*
- **Published layout coverage (93.6 % / 88.1 %) is far above the ruled coverage on disk** —
  `geometry_outcome = DWELLING_LAYOUT_EMITTED*` counted the non-ruled `equal_strip_multi_angle_sweep`
  strip cutter as a success, hiding 843 buildings. Fix: `D-EU-39` §2 retired the strip cutter as a
  success path (`european_residential.py:890`, `_secondary` always returns
  `dwelling_layout_emitted=False`); confirmed 2026-08-31 — **0 side-cars carry the strip scheme**. The
  refusals it produced did **not** become ruled layouts: coverage went 57.81 % → 56.92 %.
  *(`FINDING 207` → `FINDING 211`)*

---

## 2. Extrusion, interzone surfaces and EnergyPlus geometry fatals

- **`Severe RoofCeiling:Detailed="BLOCK <stem>_CIRCULATION STOREY 0 CEILING 0001_2", Vertex size mismatch
  between base surface … and outside boundary surface: …_CIRCULATION STOREY 1 FLOOR 0001_1` (8 vs 9
  vertices), then `**FATAL:GetSurfaceData: Errors discovered, program terminates.` — task dies in 2–4 s
  with `ExitCode 1:0`, before warmup, on ~8 % of an array** (`FINDING 210`, wave 1 of `EU-16` T09;
  example task `1299912_33`, stem `8b3598ac47b3f4a0`, Madrid) — geomeppy's own `intersect_match` cuts a
  same-zone-label block (the carved circulation ring spans every storey under one label) against its
  per-storey neighbours and inserts intersection vertices **independently** for the ceiling of storey *n*
  and the floor of storey *n+1*, so the two rings end up with different final vertex counts even though
  the ring emitted going in was identical and already 1 mm-snapped. Fix: detect and reroute —
  `find_mismatched_interzone_pairs` then `_force_reroute_room_layout_to_one_zone_per_floor`
  (`scripts/run_eu_s2_campaign.py:516-534`, implementation `openubem/idf/surfaces.py:640`).
  🔴 **Read chapter 3 before treating this as closed** — the reroute silently costs the building its
  dwelling zoning and its core. *(prompts/DIRECTOR_PROMPT_european_locations.md item 0a; STATE v4 §3)*
- **The same fatal with the raw vertex counts *matching* (both surfaces 7 vertices, mirror-ordered) —
  `find_mismatched_interzone_pairs` reports 0 mismatches and EnergyPlus still fatals** (`D-EU-43`
  residual; reproduced locally on stem `e21bec78b937acf5`) — a sub-mm near-duplicate vertex pair that
  `intersect_match` inserted into **both** rings (one grid-clean from the 1 mm snap, the other an
  unsnapped raw intersection coordinate ~0.2–0.6 mm away); EnergyPlus's duplicate-vertex removal is
  winding-direction-dependent and collapses the two sides differently (4 vs 6). Fix:
  `_has_near_duplicate_vertex_surfaces` (`scripts/run_eu_s2_campaign.py:94`) gates on consecutive-vertex
  proximity so the reroute fires proactively instead of on a count that this defect does not always move.
  *(debugs/docs/INVESTIGATION_bologna-failure-classification_2026-08-31.md)*
- **A whole district's IDFs predate a geometry fix and fail with a signature already known and already
  fixed — Bologna 177 `FAILED` of 1,204, split 85 exact `FINDING 210` + 52 exact `D-EU-43` + 40
  zero-area-only** — the fix was applied and Madrid / Lyon / London were rebuilt; Bologna was not, so its
  IDFs still carried the old geometry. Fix: rebuild through the unmodified gate and resubmit
  (`D-EU-47`). Rule this teaches: after a geometry fix, **enumerate which districts' artefacts were
  actually rebuilt** — a per-district mtime histogram of `idfs/*.idf` answers it in one command.
  *(debugs/docs/INVESTIGATION_bologna-failure-classification_2026-08-31.md)*
- **`** Warning ** Indicated Zone Volume <= 0.0 for Zone=…` / `The calculated Zone Volume was=-49.03` /
  `… set to 10.0 m3`, together with `GetVertices: Floor is upside down! Tilt angle=[0.0]`** — OSM
  footprints arrive clockwise-wound and the by-storey extrusion path uses them unoriented, so the
  divergence-theorem volume integrates negative and EnergyPlus substitutes a fixed 10 m³. **Not cosmetic
  where infiltration/ventilation is `AirChanges/Hour`**: measured in the EU S2 campaign, 103/103 zones in
  31/31 buildings, 1,030.0 m³ of air simulated against a true 59,470.92 m³ — a **57.74× understatement**;
  re-winding without repairing the volume still leaves −11.8 % on heating demand, with EnergyPlus's own
  reported floor area, volume, wall area and surface count byte-identical between the two runs. Fix:
  `orient(poly, sign=1.0)` before `build_zones`, and `write_zone_volumes(idf, zones)` after
  `extrude_geometry` (`openubem/idf/builder.py:217`). ⚠ Trap when sizing the error: do **not** take
  |calculated volume| as the truth — read `Ceiling Height` and `Floor Area` from `eplusout.eio`.
  *(debugs/docs/DONE-docs/DECISION_REQUEST_EU-17_zone_volume_10m3_2026-08-26.md;
  docs_EXPLANATION/OpenUBEM_debug_References.md ch. 1, ch. 14)*
- **A geometry fix proven by a Python-only vertex-count check passes, and the same buildings still fatal
  on real EnergyPlus** (progress-log entry `T09-FINDING210-ROOTCAUSE-FIX-V2`) — the defect is created by
  EnergyPlus's own `GetVertices`/`CheckConvexity` collapse, downstream of anything a shapely-level check
  can see. Fix: no geometry change ships on synthetic proof. Run
  `ExpandObjects.exe` + `energyplus.exe` 23.1.0 locally on at least one building per failure signature
  and report RC and severe/fatal counts. *(prompts/previous/PROMPT_D-EU-47_bologna_rebuild_resubmit.md
  §Task item 3)*

---

## 3. The viewer vs the simulated IDF

🔴 **This is the arc's most recurrent defect class — three occurrences, three different mechanisms, one
symptom: the pop-up shows geometry that never ran.**

- **[OPEN] The side-car declares `has_unconditioned_core = true` and a ruled grid; the IDF that ran is
  `<stem>_F0_whole`, `<stem>_F1_whole`, … — one undivided zone per floor. 459 of 2,544 buildings
  (Madrid 175, Lyon 52, London 18, Bologna 214); only 2 of them disclose it** (`FINDING 213`, measured
  2026-08-31) — the `FINDING 210` safety net (chapter 2) reroutes **inside** `build_idf_for_building`,
  unioning the storey-0 sub-zones back into one block per floor and dropping the circulation zone with
  them (`openubem/idf/surfaces.py:640`). The disclosure that writes it back into `geometry_outcome`
  exists (`scripts/run_eu_s2_district_campaign.py:387-390`) but was added 2026-08-31, after the IDFs of
  2026-08-30 were built; and the side-car emitter regenerates the layout from the footprint
  (`scripts/emit_eu11_layout_sidecars.py`), so it never learns of the reroute at all. Fleet effect:
  **1,555 of 2,544 IDFs (61.1 %) are one zone per floor** while the side-cars report 43.1 % refused.
  Fix: not fixed — `EU-18`'s parity gate. Diagnostic in one command:
  `grep -lE "_F[0-9]+_whole,[ ]*!- Name" <district>/idfs/*.idf | wc -l`. *(STATE v4 §3 `FINDING 213`)*
- **`geometry_outcome` is computed before the IDF is built, so any in-build reroute leaves it stale** —
  `scripts/run_eu_s2_campaign.py:681-692` records the outcome from `build_geometry_for_row` and only then
  calls `build_idf_for_building`, which may reroute. Fix: the district path now re-derives the outcome
  from the zones after the build (`scripts/run_eu_s2_district_campaign.py:387-390`, 2026-08-31); the
  single-district path at `run_eu_s2_campaign.py` still does not. *(same)*
- **`EU-13`'s `geometry_outcome` disagreed with the `heating_kwh` / `floor_area_m2` already harvested for
  the same building — `relation/12582232` labelled `DWELLING_LAYOUT_EMITTED` with
  `floor_area_m2 = 1089.2873`, exactly 272.32 m² × 4 storeys, the massing-box total** — the side-car
  emitter recomputed the outcome and the pop-up zones from the footprint alone, entirely independent of
  `run_eu_s2_district_campaign.py:_geometry`, the function that actually built the submitted zones; that
  function's layout branch omitted `n_storey=` and its `else` branch had no dwelling-count imputation, so
  most newly-labelled buildings had in fact been simulated under older massing-box zoning. Fix:
  `_geometry` now mirrors the emitter exactly — same stacking, same four-tier imputation, same outcome
  strings (`scripts/run_eu_s2_district_campaign.py:112`). ⚠ **That fix made the two *generators* agree
  and cannot see the entry above, which happens downstream of both.**
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. "European locations X-05"; `D-EU-35`)*
- **The four viewers looked visually unchanged after `EU-13B`'s ruled math landed — no circulation ring
  anywhere** — the ruled partitioner computed a real per-storey circulation polygon, but
  `scripts/emit_eu11_layout_sidecars.py` discarded it before serialization and the viewer's
  `drawFloorPlan` had no code path to draw it. Fix: both scripts carry and draw the ring; unit test
  covers the ruled-grid (non-null) and `l_shape_decomposition` (`None`, pinned) cases; all four districts
  regenerated and mirror-verified. `FINDING 206`, fixed 2026-08-30.
  *(debugs/docs/INVESTIGATION_viewer-circulation-not-drawn_2026-08-30.md)*

---

## 4. Context geometry, shading and adiabatic party walls

- **`0` of 2,516 district IDFs contained a single `Shading:*` object or a single `Adiabatic` surface,
  while the method of record requires every building within 20 m as shading and adiabatic party walls**
  (`FINDING 208`) — one line: `extrude_geometry(idf, zones, [])` hard-coded an empty context list
  (`scripts/run_eu_s2_campaign.py:227` at the time), and no `ShadowCalculation` object existed. Fix:
  `build_european_context` + `apply_adiabatic_party_walls` wired into the district path (`EU-16` T06/T07).
  Re-measured 2026-08-31: **shading on 2,544 of 2,544 (100 %)**. *(rules/RULES_context_geometry_simulation_2026-08-30.md)*
- **`grep "Shading:" *.idf` returns zero on IDFs that do carry shading** — object names are written
  **UPPERCASE** on disk (`SHADING:SITE:DETAILED`), so a case-sensitive grep silently reports a false
  absence. Fix: always `grep -i`. This one has already produced a wrong "before" number once in this arc.
  *(prompts/PROMPT_EU-VAL_validation_audit_T10.md §(c))*
- **`set_adiabatic_surfaces(idf, zones, strategy)` cannot implement the inter-building party-wall flip,
  although two rule documents said it should** — it is a documented **no-op stub**
  (`openubem/idf/surfaces.py:909`) and its signature carries no neighbour footprints, so it can never
  know which wall is shared. Fix (`D-EU-41`, 2026-08-30): `openubem/idf/surfaces.py` stays non-editable;
  the flip is a European-only pass in `scripts/run_eu_s2_campaign.py` reusing `build_european_context`'s
  own neighbour rows and transform. Disclosure required with it: **flipped exterior wall area as a
  fraction of total exterior wall area** — an object count cannot distinguish one wall from half an
  envelope. *(rules/RULES_context_geometry_simulation_2026-08-30.md §2 `R6`)*
- **[OPEN] Adiabatic coverage is 89.4 / 86.5 / 70.7 / 80.7 % (Madrid / Lyon / London / Bologna) against
  an attachment census expecting 99.1 / 97.0 / 92.8 / 88.5 %** — measured by `EU-16A` T08, re-measured
  identically 2026-08-31 (859 / 257 / 58 / 972 IDFs carrying an `Adiabatic` surface). Reported as
  measured, never tuned, and **not explained anywhere on disk**. *(STATE v4 §3)*
- **[OPEN] London's mean context count is 7.52 neighbours against 11.60 in the rules-doc census; the
  other three agree to ±0.4** — measured over `prepared_buildings.csv:context_building_count`
  (Madrid 11.88, Lyon 12.28, London 7.52, Bologna 11.22; zero buildings with an empty context). Note this
  **supersedes** the `EU-16A` audit's carried claim of 30.1–49.1 neighbours, which does not reproduce on
  today's artefacts. *(STATE v4 §3)*

---

## 5. Areas, denominators and EUI arithmetic

- **A manifest column named `eui_kwh_m2` that is in fact a heating-only intensity** — the numerator is
  `heating_kwh`, the annual sum of hourly `Zone Ideal Loads Zone Total Heating Energy`; it carries no
  lighting, no appliances, no DHW, no cooling, so quoting it as a whole-building EUI is wrong by a large
  factor **in the direction that looks plausible**. Fix: the promoted artefact is not renamed; the basis
  is carried additively and no pooled figure is printed without the words "heating-only".
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 8; previous/MVP_european_locations.md §9.7.3)*
- **[OPEN] `floor_area_m2` equals `gross_footprint_area_m2` on 2,544 of 2,544 rows and
  `conditioned_floor_area_m2` on none, although `D-EU-39` §3 ruled that carving the core moves every EUI
  denominator** (`FINDING 214`) — `scripts/run_eu_s2_district_campaign.py:408-418` assigns the gross sum
  to `floor_area_m2`. Both areas are published side by side, so the disclosure half of the ruling is met
  and the arithmetic half is not. Effect on the 582 buildings that carry a core: conditioned/gross means
  0.9551 / 0.9598 / 0.9083 / 0.9359, minimum 0.5189. Fix: not fixed — must be settled explicitly before
  any figure is restated. *(STATE v4 §3 `FINDING 214`)*
- **`gross_footprint_area_m2` is not a footprint area** — it is the building total, summed once per
  storey **group** (`european_building_layout_area_summary`, `openubem/geometry/european_residential.py:1904`),
  while `circulation_area_m2_total` is summed over physical storeys. The two are consistent
  (conditioned + circulation − gross ≤ 1.2 × 10⁻⁶ relative, measured fleet-wide) but the name invites a
  per-floor reading and a spurious ×storeys conservation failure. Diagnostic: check
  `conditioned + circulation == gross` **without** multiplying by `storeys`. *(STATE v4 §3)*

---

## 6. Speed: submission, walltime, harvest, tcsh

- **9 Lyon array tasks end in `TIMEOUT`, `eplusout.err` empty, no `task.rc`, working files present** —
  genuine wall-clock exhaustion, not a defect: all 9 exceeded the 2-hour limit by **0–28 s**
  (`scripts/cluster/submit_fleet_t08.sbatch:5`, `--time=02:00:00`), 8 of the 9 in the ≥72nd percentile of
  floor area. Fix: never edit the shared sbatch — override on the command line
  (`sbatch --time=… --array=…`). 🔴 **A 3 h override was then observed to time out twice as well**, so the
  standing rule is `--time=7-00:00:00` minimum on every submission: SLURM bills actual usage, a generous
  request costs nothing, and it removes the resubmit cycle entirely.
  *(debugs/docs/INVESTIGATION_lyon-timeout-classification_2026-08-31.md; BRIEF_european_locations_v3.md §5;
  CLAUDE.md §CLUSTER)*
- **A harvest finds nothing under `openubem/fleets/EU11R2_<district>/`** — those are **upload staging**
  entries (`.tgz` + `.submit.sbatch`) only; a missing one is harmless. The arrays run
  `submit_fleet_t08.sbatch` with `FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_<district>`, so results
  live at `/speed-scratch/o_iseri/fleets/EU11_<district>/out/<stem>/`. Fix: harvest the `EU11_*` tree; a
  resubmit wave ships to its own dedicated dir (`EU11_<district>_deu47`) and never overwrites the shared
  base tree in place. *(prompts/DIRECTOR_PROMPT_european_locations.md item 0a)*
- **`sbatch` fails, script not found** — the remote path was guessed flat as
  `/speed-scratch/o_iseri/openubem/scripts/submit_fleet_t08.sbatch`; it is nested:
  `…/scripts/cluster/submit_fleet_t08.sbatch`. Fix: use the `cluster/`-nested path in every call.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 12)*
- **A remote command sent over bare `ssh` silently does nothing, or dies on a `!` in the string** — the
  Speed login shell is **tcsh**: bash syntax fails silently and `!` triggers history expansion. Fix: wrap
  every remote command in `bash -lc` via the repo's `_ssh()` helper
  (`scripts/cluster/t08_harvest_results.py:104`), and never put `!` in a remote command string.
  *(CLAUDE.md §CLUSTER)*
- **Every array task fails instantly with `Schedule:File=… not found`** — `ship_eu11_fleet.sh` staged and
  tarred only `idfs/`, `weather/`, `fleet.lst`, never the local `schedules/` directory, so the remote
  fleet had no schedule CSVs at all (100 % failure across Madrid 961, Lyon 297, London 82). Fix: stage
  and tar `schedules/` too; re-shipped and resubmitted clean.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 12)*
- **`FileExistsError: [WinError 183]` on `schedules/<stem>/`** — a preparer that unconditionally
  `mkdir()`s into a tree left over from a previous preparation (no `exist_ok`, no cleanup). Seen twice, at
  two call sites: `ship_eu11_fleet.sh`'s staging step, and `run_eu_s2_district_campaign.py::prepare`
  itself (`:347`). Fix: clear `idfs/`, `weather/`, `schedules/`, `fleet.lst` under
  `openubem/outputs/eu_evidence/EU-11/<district>/` before every `prepare()` re-run — otherwise stale
  CSVs from a superseded regeneration leak into the new tar.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 12, "European locations EU-13B")*
- **Never compute on the login node** (`speed-submit2` / `speed.encs.concordia.ca`) — no `srun`, no
  `ssh … python`. Login node is `mkdir` / `scp` / `tar` / `squeue` / `sacct` only. Always
  `sbatch --array`, fire-and-forget, then read the output file. Submit in waves under the ~20,000-task
  cap; harvest by expanding file lists **remotely** and streaming a tar (a local path list overflows
  Windows argv at ~32 KB). *(CLAUDE.md §CLUSTER)*

---

## 7. Schedules, weather and file paths

- **`Schedule:File=…, File Name: "C:\Users\…\*_gain.csv" not found` on Speed** — the accepted S2 builder
  emits an **absolute Windows** schedule path, valid locally and meaningless on Linux once the IDF alone
  is staged. Fix: `run_eu_s2_district_campaign.py::prepare` stages the byte-identical gain CSVs under
  `schedules/<stem>/` and retargets only each `Schedule:File` path to `../../schedules/<stem>/…`,
  relative to the array task's output directory.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. "European locations EU-10")*
- **`FileNotFoundError` on `…/ES-MAD-BERRUGUETE/relation/12582232/relation/12582232.idf` the first time a
  runner met a Spanish building** — OSM stable ids are `way/123` / `relation/456` and the **slash is a
  path separator**, so every place that names a file after `building_id` silently opens a directory
  level: run directory, IDF, zone names, and each `Schedule:File` CSV. France never exposed it because
  BD TOPO ids (`BATIMENT0000000240879449_part0`) carry no slash — a runner can pass every French test and
  still be unable to write its first Spanish IDF. Fix: a `run_slug` that maps `/` to `_` for **naming
  only**, with the true `building_id` kept beside it in the manifest.
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 7)*
- **`ERROR: Could not find input data file: <dir>\<dir>\<name>.idf`, `returncode=1`, no `eplusout.err` at
  all** — the runner built its temp directory from a **relative** `Path` and passed the still-relative
  `idf_path` alongside `cwd=tmp_root`; `cwd=` does not rebase relative path *arguments*, so EnergyPlus
  resolved it a second time against the new working directory. Fix: `.resolve()` the temp directory
  before building the `.idf` path from it (`scripts/run_eu_s1_smoke.py:283`).
  *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. 13)*

---

## 8. Data acquisition per country

Full entries live in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` **ch. 7**; this is the routing
list, so an arc session knows the symptom has been seen before.

- `HTTP Error 429 / 504` from `overpass-api.de/api/interpreter` on city-scale extracts.
- Building counts silently wrong when a WGS84 bbox is passed to `ingest_buildings` in GeoJSON order.
- A residential filter over OSM tags returns almost nothing in Italian and French cities.
- `data.geopf.fr` WFS `GetFeature` returns `"features": []` with HTTP 200 and no error.
- `HTTP 400 "No se puede procesar su peticion."` from the Spanish Catastro INSPIRE Buildings WFS — it
  answers a bbox question in exactly one parameter form, and any other form fails as an HTTP error.
- `curl` returns `HTTP 000` with 0 bytes for `catastro.minhap.es/INSPIRE/…` while the same path works
  under another host.
- The MHCLG/EPC endpoint pinned by `D-EU-10` is retired; its successor sits behind an account, and the
  old one answers `301` onto a GOV.UK landing page.
- ISTAT 2011 section breakdowns do not sum to the residential-building total (`E4+E5+E6 = 1,140` vs
  `E3 = 1,010`); and a zero join rate is a broken probe until proven otherwise — the ISTAT section key is
  **`NSEZ`**, not `SEZ2011`.
- `URLError [SSL: CERTIFICATE_VERIFY_FAILED]` against the Emilia-Romagna geoportal.
- A UPRN-to-footprint spatial join silently loses ~13 % of its pairs (London: 1,059 footprints instead of
  the pinned 1,219), with no error and no warning.
- Bologna construction period is `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on **100 %** of rows —
  never quote a Bologna figure without saying so. *(EU11_Bologna_construction_year_investigation.md)*

---

## 9. Reproducibility and certification traps

- **A campaign cell exits `0`, is recorded `completed: true`, `severe_count: 0`, `fatal_count: 0`, no
  `.err` marker — and returns a different heating value on the next identical run** — measured at
  429,401.898 kWh twice and 111,864.121 kWh once (−74.0 %) for
  `uk__GB.ENG.AB.03.Gen.ReEx.001.001__f000`, strictly serial, from a byte-identical model. Fix: none —
  `D-EU-27` certifies a cell only when **three** independent replicates return a bitwise-identical
  `heating_kwh` with zero severes and zero fatals; the worst disagreement that filter rejected was
  382.1 %, so it must never be relaxed to two of three.
  *(implementation/previous/PLAN_finding181-stability-2026-08-28.md §7)*
- **[OPEN] `completed: true` and `clean: true` are each necessary and NOT sufficient** — EnergyPlus
  reports the diverging inside-surface heat balance as a **Warning**, which raises neither counter, so
  `marker_psy` / `marker_inside_hb` / `marker_calchb` must be screened from `eplusout.err` as well.
  42 certified cells carry `marker_psy` in all three replicates and **all 42 are `es`**; `D-EU-28`
  restricts the quotable perimeter to the 149 marker-free certified cells (`uk` 75, `it` 74, `es` 0).
  *(previous/MVP_european_locations.md §9.7.3)*
- **`idf_sha256` differs between two runs of the same cell although the model is identical** — the
  `Schedule:File` `File Name` field holds the **absolute** path (`openubem/semantic/european_schedules.py:119`),
  so the digest embeds the run directory. Fix: none applied — the digest is a run identifier, not a
  model-provenance key. *(implementation/previous/PLAN_finding181-stability-2026-08-28.md §7)*
- **A Speed number and a Windows number are not the same measurement** (`FINDING 187`, `FINDING 190`) —
  EnergyPlus 23.1.0 Ubuntu20 on Speed and 23.1.0 on Windows do not agree bitwise. Never mix them inside
  one pooled figure, and never validate a Speed result by re-running it locally and calling the local
  answer the truth.

---

## 10. Method traps

- **A reason token emitted by fall-through is not evidence of that failure mode.** `HABITABILITY_GATE_
  FAILED_AFTER_ROTATION` on 84 % of the fleet was an empty-intersection bug (ch. 1). Check the cell count,
  the vertex count, the actual intermediate — not the label.
- **Measure conformance on the artefact that ran, never on the layer that describes it.** Side-cars said
  43.1 % refused; the IDFs said 61.1 % boxes. Both were on disk at the same moment (ch. 3).
- **A synthetic check is not proof for a defect EnergyPlus creates.** (ch. 2)
- **Read what a warning says; do not count warning kinds.** A triage gate that only counts is satisfied
  by six kinds of which two invalidate the result. *(zone-volume entry, ch. 2)*
- **After a fix, enumerate which artefacts were actually rebuilt.** Bologna carried 177 failures of a
  signature that had already been fixed, purely because its IDFs were never regenerated (ch. 2).
- **A 0-byte log is not a dead job, and an ambiguous status is not a reason to double-dispatch.** Check
  CPU time first (`sacct`), then decide.
- **Never tune an input to move an EUI into a band**, and never remediate a baseline while measuring it.

---

## 11. Not-a-bug: by design in this arc

- **`>8 dwellings/floor` is refused, not approximated** (`FINDING 202`, `D-EU-39`) — 75 buildings, 18 of
  them London. Fail-closed is the design; the count is never reduced to fit the grid.
- **`l_shape_decomposition` serialises `circulation: None` even when its wings carried circulation** —
  `keep_circulation_polygon=False` (`openubem/geometry/european_residential.py:977`), pinned by a unit
  test. The area is kept, the drawable ring is dropped. Currently costs nothing measurable (0 floors
  fleet-wide with area but no polygon) but it **will** un-draw the L-shape cores `EU-17` creates —
  revisit it there. *(FINDING 206 follow-up; STATE v4 §3 `FINDING 212`)*
- **`ruled_grid_1x1` carries no circulation** — one dwelling per floor takes the whole plate
  (`european_residential.py:873-887`); there is nothing to circulate between. 401 buildings fleet-wide.
- **A single-storey building carries no circulation** — ruled 2026-08-31 (`D-EU-49`). 46 buildings; the
  3 that currently carry a core lose it.
- **The S0 equivalent-envelope geometry warnings** (`Floor is upside down`, `zone is not fully enclosed`,
  `Entered Zone Floor Area(s) differ more than 5%`) are inherent to that method
  (`openubem/idf/european_box.py:48-58`) and, since the `InternalMass` repair, no longer produce
  non-determinism. *(docs_EXPLANATION/OpenUBEM_debug_References.md ch. "European locations X-05")*
