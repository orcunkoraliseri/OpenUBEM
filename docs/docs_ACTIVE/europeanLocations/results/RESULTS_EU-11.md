# RESULTS_EU-11 — full district campaign on Speed, harvested

- **Arc**: European locations × Step 8. Executor prompt:
  [`prompts/PROMPT_EU-16B_speed_resimulation_T09.md`](../prompts/PROMPT_EU-16B_speed_resimulation_T09.md).
  Plan: `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` §8.
- **This revision (2026-08-31) replaces a prior version of this file written by a session that was
  terminated mid-flight** (renamed to `RESULTS_EU-11.md.STALE_killed-session-2026-08-31`, kept for record,
  not used as a source here). That session's own recovery-wave job IDs and per-district recovery counts were
  independently found to be wrong (it measured a **cancelled**, intermediate `v3` attempt — jobs
  `1302881`/`1302908`/`1302920` — not the real, corrected, completed wave). This document is built from a
  fresh harvest of the actually-completed jobs, `sacct`-verified.
- **Date harvested**: wave 1 (`ES-MAD-BERRUGUETE` `1299912`, `FR-LYO-HAUTCOEURPENTES` `1299945`,
  `GB-LDN-STDUNSTANS` `1299946`, `IT-BOL-GALVANI2` `1299947`) 2026-08-30/31, harvested by a prior session;
  `D-EU-42`/`D-EU-43` recovery wave (`1302937` Madrid 43 tasks, `1302954` Lyon 8 tasks, `1302962` London 1
  task) 2026-08-31, all 52 tasks `sacct`-confirmed `COMPLETED`/`0:0`, harvested that session; `D-EU-44`
  recovery wave (`1303012`, Madrid 2 tasks) 2026-08-31, both tasks `sacct`-confirmed `COMPLETED`/`0:0`,
  harvested this session. Harvest script: `scripts/cluster/harvest_eu11_district.py` (wave 1) + ad hoc
  fold-in scripts (this and the prior session, `D-EU-42`/`D-EU-43`/`D-EU-44` rows only — see the findings
  below).
- **Scope**: S2 real-footprint perimeter, `f = 0` (uninjected baseline), heating only. Not the frozen S0
  archetype campaign (149 cells); not compared to it.

## Per-district results (current, post-`D-EU-42`/`D-EU-43`/`D-EU-44` fold)

| District | attempted | prep-excluded | run on Speed | success | Speed-failed | pooled heating EUI |
|---|---:|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 1,194 | 233 | 961 | **961** | **0** | **72.1096 kWh/m²** |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 233 | 297 | 288 | 9 | **62.1528 kWh/m²** |
| `GB-LDN-STDUNSTANS` | 1,242 | 1,160 | 82 | 82 | 0 | **78.4405 kWh/m²** |
| `IT-BOL-GALVANI2` | 1,220 | 16 | 1,204 | 1,014 | 190 | **48.9253 kWh/m²** 🔴 imputed period |

Madrid is now **100 % recovered** (961/961) after `D-EU-44` (see below) — the pooled EUI moved
72.1258 → 72.1096 kWh/m² (2 buildings of 961).

Manifests: `openubem/outputs/eu_evidence/EU-11/<DISTRICT>/<district_slug>_manifest.csv`. Post-run summaries:
`.../summary.json` (pre-run kept as `summary_prerun.json`).

Bologna is **unchanged from wave 1** — `D-EU-42`/`D-EU-43` were scoped to Madrid/Lyon/London only; Bologna's
177 wave-1 fatals + 13 timeouts were never in scope for any recovery wave and remain fully disclosed, not
addressed. **Every Bologna EUI figure in this document carries `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD`
provenance** — construction period is imputed by ISTAT 2011 census-section spatial join, never
`OBSERVED_YEAR`, and 100 % of Bologna's dwelling counts are imputed-count.

## `D-EU-42` / `D-EU-43` recovery — what this harvest found

Wave 1 (`sacct`-confirmed, plan §8): Madrid 863 `COMPLETED` / 98 `FAILED` / 0 `TIMEOUT` (961); Lyon 262 / 26 /
9 (297); London 80 / 2 / 0 (82); Bologna 1,014 / 177 / 13 (1,204). Every Madrid/Lyon/London `FAILED` task
carried either the `FINDING 210` vertex-size-mismatch signature (`D-EU-42` scope: 66 Madrid, 13 Lyon, 2
London) or the zero/negative-surface-area signature (`D-EU-43` scope: 32 Madrid, 13 Lyon) — full root-cause
history in `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, "European locations EU-16" chapter
(`FINDING 210`, `D-EU-43`).

The real root cause (not ring construction — `_stabilize_ring_coords`,
`openubem/geometry/european_residential.py:1825`, was already correct) is `geomeppy`'s own
`intersect_match()` (`openubem/idf/surfaces.py:866`, non-editable per `D-EU-41`), which computes new
boundary vertices independently per surface, post-extrusion, and can leave a storey's ceiling and the
storey-above's floor with different final vertex counts, or a sub-mm near-duplicate vertex, or a
machine-precision-collinear vertex — three distinct failure shapes EnergyPlus's own convexity/vertex-pairing
checks catch differently. Fix: `scripts/run_eu_s2_campaign.py::build_idf_for_building` now calls
`find_mismatched_interzone_pairs` right after `extrude_geometry` and, if any remain, reroutes via
`_force_reroute_room_layout_to_one_zone_per_floor` (both pre-existing in `openubem/idf/surfaces.py`, used
here for the first time by the EU S2 campaign path); `_has_near_duplicate_vertex_surfaces`
(`scripts/run_eu_s2_campaign.py`, new) additionally gates on near-duplicate vertices
(`NEAR_DUPLICATE_VERTEX_TOLERANCE_M = 0.005`) and machine-precision collinearity
(`COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG = 0.1`). Proven locally (0/52 `FATAL` under real EnergyPlus
23.1.0), then rebuilt and resubmitted as jobs `1302937`/`1302954`/`1302962` (43 Madrid + 8 Lyon + 1 London,
52 stems total). **All 52 array tasks `COMPLETED`, exit `0:0`** (`sacct -j 1302937,1302954,1302962
--format=JobID,State,ExitCode -X`), harvested and folded in for this document.

Recovery, this fold, per district:

| District | wave-1 `FAILED` (`D-EU-42`+`D-EU-43`) | recovered by this wave | still failing after this wave |
|---|---:|---:|---:|
| Madrid | 98 | 98 | 0 (2 recovered separately by `D-EU-44` — see below) |
| Lyon | 26 | 26 | 0 (Lyon's 9 remaining failures are wave-1 `TIMEOUT`s, out of `D-EU-42`/`D-EU-43` scope) |
| London | 2 | 2 | 0 |

*(Table above counts the 2 `D-EU-44` stems as recovered under Madrid's 98, since they belong to the same
wave-1 `FAILED` population; they were rebuilt/resubmitted separately, not inside jobs `1302937`/`1302954`/
`1302962` — see the `D-EU-44` section below.)*

🔴 **Separate finding, this harvest: the base `EU11_<district>/out/` tree held stale, non-Speed data for
exactly the 52 `v3`-scope stems**, predating this harvest. `find EU11_ES-MAD-BERRUGUETE/out -maxdepth 2
-name platform.txt | wc -l` = 918/961 (43 missing = exactly Madrid's `v3` scope); Lyon 289/297 (8 missing);
London 81/82 (1 missing) — every normal Speed task writes `platform.txt`/`energyplus_version.txt`, confirmed
on untouched stems. Stem `8b3598ac47b3f4a0`'s base-tree copy showed `task.rc=0`/"Completed Successfully" at
mtime `2026-08-31 14:58:32`, which **predates** job `1302937`'s own per-task completions (15:13–15:19) — a
leftover of an earlier local-Windows `EnergyPlus` proof run, copied into the base tree by an undocumented
step, not a Speed measurement. **This harvest did not trust the base tree for these 52 stems** — it read
directly from `EU11_<district>_finding210v3/out/<stem>/` (the job's own output, `sacct`-confirmed) for all
52 rows. `platform`/`energyplus_version` are blank for these 52 rows in the manifest: the `_finding210v3`
resubmission's own output also lacks those two sidecars (confirmed via the same `tar` fetch), a property of
that resubmission's script invocation, unrelated to the contamination above.

## `D-EU-44` — the 2 unaccounted Madrid stems, recovered

Owner authorisation, verbatim: *"oui, autorise D-EU-44 continuer jusqu'a la fin"* (owner, 2026-08-31, replying
to the manager's proposal to fix, rebuild, and resubmit exactly these 2 stems). `df490cc7ec52ebb4`
(`way/380242666`) and `5897ad5bdd60c3ae` (`way/941927233`) carried the identical `FINDING 210`
degenerate-surface fatal class as the 52-stem `D-EU-42`/`D-EU-43` population but were never enumerated into
the 43-stem Madrid `v3` `fleet.lst` and were never resubmitted.

Both were rebuilt through the exact same fixed code path (`scripts/run_eu_s2_district_campaign.py::prepare`'s
per-building loop, filtered to these 2 `building_id`s, calling `scripts/run_eu_s2_campaign.py::
build_idf_for_building`). The gate fired for both — `rerouting room_layout to one_zone_per_floor
(near_duplicate_vertex)` — confirming the same `FINDING 210` mechanism applies. **Local proof, real
EnergyPlus 23.1.0 (Windows, `ExpandObjects.exe` + `energyplus.exe`, matching
`submit_fleet_t08.sbatch`'s invocation):** both rebuilt IDFs ran with `RC=0`, `0 Severe Errors`, `0 Fatal
Errors`, `EnergyPlus Completed Successfully` — no vertex-mismatch signature, ground truth not a Python-level
heuristic. Rebuilt IDFs confirmed byte-identical (`sha256sum`) between the local proof build and the tarball
actually shipped to Speed.

Shipped to a dedicated fleet dir (`/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_deu44`, never
overwriting the shared `EU11_ES-MAD-BERRUGUETE` base tree) and submitted as **one** `sbatch --array=1-2%2`
job: `1303012`. `sacct -j 1303012 -X --format=JobID,State,ExitCode,Elapsed` confirms both tasks
`COMPLETED`/`0:0` — `1303012_1` (`df490cc7ec52ebb4`) 00:02:36, `1303012_2` (`5897ad5bdd60c3ae`) 00:07:24.
Both `eplusout.err` on Speed also show `0 Severe Errors`/`EnergyPlus Completed Successfully`, matching the
local proof exactly (Speed, not just Windows, confirmed clean).

Recovered heating figures (harvested this session, `Zone Ideal Loads Zone Total Heating Energy`, J → kWh):

| stem | `building_id` | `geometry_outcome` | `floor_area_m2` | `heating_kwh` | `eui_kwh_m2` |
|---|---|---|---:|---:|---:|
| `df490cc7ec52ebb4` | `way/380242666` | `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` | 438.6929 | 22995.2274 | 52.4176 |
| `5897ad5bdd60c3ae` | `way/941927233` | `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` | 194.5278 | 7352.8695 | 37.7986 |

`floor_area_m2` for both moved slightly from the pre-fix `DWELLING_LAYOUT_EMITTED` value (439.0326 →
438.6929; 195.5908 → 194.5278) because the reroute measures the union of per-storey floor polygons instead
of the per-dwelling partition — the same effect already disclosed for the other 50 `D-EU-42`/`D-EU-43`-scope
reroutes. `platform`/`energyplus_version` are blank for these 2 rows in the manifest — the same missing
`platform.txt`/`energyplus_version.txt` sidecar gap already registered `[OPEN, cosmetic]` in
`OpenUBEM_debug_References.md`'s EU-14B chapter (the remote-deployed `submit_fleet_t08.sbatch` does not write
them), not a new defect.

Both stems folded into `es_mad_berruguete_manifest.csv` and `prepared_buildings.csv`, replacing the two
`FATAL`/blank rows. Madrid: **961/961 success, 0 Speed-failed** — no residual `FINDING 210` casualties remain
anywhere in the 2,544-building EU-11 fleet outside Bologna's separately-scoped, unaddressed 190 (out of
`D-EU-42`/`D-EU-43`/`D-EU-44` scope).

## Before/after EUI — `EU-15`+`EU-16` vs pre-`EU-15`/`EU-16` (`EU-13B`/`EU-14B`), sign explained

Per `rules/RULES_context_geometry_simulation_2026-08-30.md` §3 acceptance-test item 5. `EU-13B`/`EU-14B`
figures independently re-verified against `openubem/outputs/eu_evidence/EU-13B/RESULTS_EU-13B.md` and
`.../EU-14B/RESULTS_EU-14B.md` (not taken from the stale file).

| District | pre-`EU-15`/`EU-16` (`EU-13B`/`EU-14B`) | post-`EU-15`/`EU-16` (this harvest) | delta |
|---|---:|---:|---:|
| Madrid | 81.5325 | 72.1096 | **-9.4229 (-11.56 %)** |
| Lyon | 69.5235 | 62.1528 | **-7.3707 (-10.60 %)** |
| London | 86.8703 | 78.4405 | **-8.4298 (-9.70 %)** |
| Bologna 🔴 imputed period | 47.4921 | 48.9253 | **+1.4332 (+3.02 %)** |

🔴 This delta is **not** an isolate of `EU-16` (shading + adiabatic) alone — the same T08 rebuild also
carried `EU-15`'s ruled thermal zoning (carved circulation cores, retired strip cutter), which is not
separable from `EU-16` in this harvest (no ablation run exists). Sign, per the rule's own physics: shading
(`EU-16` T06, 100 % of IDFs carry ≥1 `Shading:Site:Detailed` in all four districts) lowers solar gain
(heating **up**); adiabatic party walls (`EU-16` T07) remove a loss path (heating **down**) — adiabatic
coverage vs the measured attachment census: Madrid 89.39 % (vs ≈99.1 % attached), Lyon 86.53 % (vs
≈97.0 %), London 70.73 % (vs ≈92.8 %), Bologna 80.73 % (vs ≈88.5 %); flipped exterior-wall-area fraction:
Madrid 30.74 %, Lyon 33.35 %, London 12.29 %, Bologna 34.90 %. `EU-15`'s carved cores add unconditioned
floor area inside the same footprint, which does not act in one predictable direction on pooled per-m² EUI.
Madrid/Lyon/London all moved **down** (net); Bologna moved **up** (net) — not uniform across districts,
consistent with the rule's statement that the net is not predictable in advance. No ablation was run; which
single effect dominates in any district is not claimed here.

## External validation (DR12–16)

Band definitions from `DeepResearch/DR13`–`DR16` (unchanged from `RESULTS_EU-13B.md`/`RESULTS_EU-14B.md`).
Band membership is a mechanical range check, not an acceptability judgment — **whether these figures are
accepted as the arc's figures is the owner's call, not stated here.**

| District | harvested EUI | DR band checked | band membership |
|---|---:|---|---|
| Madrid | 72.1096 | DR13: CONSISTENT 85.0–135.0, WORTH INVESTIGATING 70.0–84.9 / 135.1–150.0, INCOMPATIBLE <70.0 / >150.0 | WORTH INVESTIGATING (low) |
| Lyon | 62.1528 | DR14 two-track: Dwelling-Partitioned CONSISTENT 100.0–140.0 / Massing-Box-Persists CONSISTENT 55.0–80.0 | inside massing-box-persists CONSISTENT band |
| London | 78.4405 | DR15: CONSISTENT 45.0–85.0, WORTH INVESTIGATING 35.0–45.0 / 85.0–105.0, INCOMPATIBLE <35.0 / >105.0 | CONSISTENT |
| Bologna 🔴 imputed period | 48.9253 | DR16: CONSISTENT 115.0–165.0, WORTH INVESTIGATING (Low) 95.0–114.9, INCOMPATIBLE (Too Low) <95.0 | INCOMPATIBLE (Too Low) |

## Mirror check

`generate_eu_3d_viewers.py` re-run for all four districts, this session, after the `D-EU-44` fold-in
(regenerates viewer + `results.csv` from the updated manifests — Madrid's `results.csv` now 961 rows, up
from 959 — mirrors `openubem/outputs/3D/` → `../outputs_3D/`). `diff -rq` on every EU-prefixed viewer file
and data directory, run individually (not `find`/summarised), all exit 0 with **no output** (byte-identical):

```
diff -rq openubem/outputs/3D/eu_ES-MAD-BERRUGUETE_viewer.html docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_ES-MAD-BERRUGUETE_viewer.html
diff -rq openubem/outputs/3D/eu_ES-MAD-BERRUGUETE_data docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_ES-MAD-BERRUGUETE_data
diff -rq openubem/outputs/3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html
diff -rq openubem/outputs/3D/eu_FR-LYO-HAUTCOEURPENTES_data docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_FR-LYO-HAUTCOEURPENTES_data
diff -rq openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_viewer.html docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_viewer.html
diff -rq openubem/outputs/3D/eu_GB-LDN-STDUNSTANS_data docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_GB-LDN-STDUNSTANS_data
diff -rq openubem/outputs/3D/eu_IT-BOL-GALVANI2_viewer.html docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_IT-BOL-GALVANI2_viewer.html
diff -rq openubem/outputs/3D/eu_IT-BOL-GALVANI2_data docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_IT-BOL-GALVANI2_data
```

All eight commands produced zero output. FR/GB/IT are unchanged this session (only Madrid's manifest moved)
and remain byte-identical to their own prior mirror, confirming the regeneration was deterministic.

## Caveats carried forward

- **`FINDING 210` / `D-EU-43` / `D-EU-44`** — see `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`,
  "European locations EU-16" chapter, for the full root-cause and fix history. **`D-EU-44` closes the last 2
  Madrid casualties** (`df490cc7ec52ebb4`/`5897ad5bdd60c3ae`) — 0 residual `FINDING 210` failures remain in
  Madrid, Lyon, or London; Bologna's 190 wave-1 failures were never in `FINDING 210`/`D-EU-42`/`D-EU-43`/
  `D-EU-44` scope and remain fully unaddressed.
- **Lyon's 9 residual failures are wave-1 `TIMEOUT`s** (`sacct`-confirmed, matches plan §8's TIMEOUT=9),
  never in `D-EU-42`/`D-EU-43` scope, disclosed not addressed. Manifest rows show `eplus_return_code=0`,
  `severe_errors=0`, `fatal_errors=0`, blank `heating_kwh` — no `task.rc` exists remotely for these stems
  (SLURM killed the task mid-run before it could be written); the working-directory files EnergyPlus leaves
  behind (`in.idf`, `expanded.idf`, `Energy+.idd`, `epluszsz.csv`) are still present, confirming the task
  never reached its own cleanup step.
- **Bologna's 190 Speed-failed rows (177 wave-1 fatals + 13 timeouts) remain fully unaddressed** — never in
  scope for `D-EU-42`/`D-EU-43` (Bologna's wave 1 was still running when both fix waves were built).
- **`Speed ≠ Windows` (`FINDING 187`/`190`)** — extended by `FINDING 210` to geometry *validity*, not only
  simulation results.
- **Never tune an input to move an EUI into a band.** Figures above are reported as measured; band
  membership and acceptability are not decided here.
