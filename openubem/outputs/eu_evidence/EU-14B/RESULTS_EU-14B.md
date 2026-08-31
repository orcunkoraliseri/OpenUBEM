# RESULTS — EU-14B: Bologna layout binding, without corrupting its manifest

Arc: European locations x Step 8. Predecessor: `EU-13B` (grid partitioner, conservation fix,
>8/floor cap — Madrid/Lyon/London). Closes the gap `EU-14` disclosed: Bologna is simulated and
bound but had zero floor-plan pop-ups.

🔴 Every figure in this document that names `IT-BOL-GALVANI2` carries
`construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on all manifest rows
(T03 adds the matching per-side-car tag). Never quote a Bologna number without it. Population is
1,204 through T04 (before resimulation) and 1,201 from T05 onward (3 buildings newly excluded by
`IDF_ASSEMBLY_FAILED_ZeroDivisionError` when the IDFs were rebuilt — see section 5).

---

## 1. T01 — root cause and safety fix (stop-and-report point 1)

### 1.1 Root cause, with `file:line`

`scripts/emit_eu11_layout_sidecars.py`'s district dispatch (pre-fix, lines 74-77) special-cased
only `GB-LDN-STDUNSTANS` and routed every other district — Bologna included — through the generic
observed-attribute mapper `_mapped_rows` → `map_observed_building_to_tabula`
(`openubem/semantic/european_archetype_mapping.py:204`), which requires an observed `year_built`
and `building_tag`. Bologna's OSM extract carries neither: its rows are produced only by the ISTAT
2011 census-section cascade `_it_rows` (`scripts/run_eu_s2_district_campaign.py:188`), which the
real preparer `prepare()` already dispatches to correctly at
`scripts/run_eu_s2_district_campaign.py:345`. The emitter never had that branch.

Confirmed by direct call, no side effects (`_mapped_rows` makes no network calls):

```
_mapped_rows("IT-BOL-GALVANI2", gdf, records)  ->  0 mapped rows out of 1220
exclusions: {'MISSING_OBSERVED_YEAR_BUILT;UNMAPPABLE_RESIDENTIAL_TYPE': 1220}
```

With `row_map` empty, the old write (`scripts/emit_eu11_layout_sidecars.py:292`, pre-fix):

```python
manifest_df["geometry_outcome"] = [updated_outcomes.get(str(b), "") for b in manifest_df["building_id"]]
```

defaulted every one of the 1,204 rows' `geometry_outcome` to `""`, which pandas reads back as
`NaN` on the next load — corrupting the only local record of Speed job `1295646`'s harvest. This
is the exact failure disclosed in the predecessor prompt's §0 item 1 and was recovered only by a
clean re-harvest from Speed.

### 1.2 Fix (two independent changes, both required)

1. **Dispatch fix.** `emit_eu11_layout_sidecars.py` now routes `IT-BOL-GALVANI2` to `_it_rows`,
   mirroring `prepare()` exactly.
2. **Non-destructive write, regardless.** A new `safe_update_manifest_columns()`
   (`scripts/emit_eu11_layout_sidecars.py`) replaces the direct assignment. It:
   - touches only the columns it is given data for (`geometry_outcome`, `layout_json`), only for
     the `building_id`s present in that column's update dict — an unmatched row's existing value
     is left untouched, never defaulted to blank;
   - never creates a column when its update dict is empty (never widens the manifest with data it
     did not compute);
   - asserts, before writing anything, that row count and the `building_id` set are unchanged and
     that no cell that was non-null/non-blank anywhere in the manifest became null or blank
     (`_is_blank` treats both `NaN` and `""` as blank, since the historical bug's in-memory value
     was `""`, only becoming `NaN` after a CSV round-trip);
   - raises `ManifestSafetyError` and leaves the file on disk untouched if any assertion fails.

### 1.3 Safety test result

`tests/geometry/test_eu14b_sidecar_manifest_safety.py`, run against a `tmp_path` copy of the real
Bologna manifest (the checked-in file itself is never touched by this test):

```
5 passed in 0.95s
```

Covers: a legitimate full update writes correctly and leaves every non-owned column byte-identical
(`pd.testing.assert_series_equal`); a partial update never touches unmatched rows; **the exact
historical failure mode — zero matched rows — now returns the manifest unchanged** instead of
blanking it; a malformed-row fixture referencing a `building_id` absent from the manifest raises
`ManifestSafetyError` and leaves the file's bytes unchanged; a computed blank value for an
otherwise-matched, previously non-blank row also raises and leaves the file unchanged.

**Green before the real manifest was touched.** T02 ran only after this.

---

## 2. T02 — Bologna's first-ever floor-plan pop-ups

Ran the corrected emitter for real against `IT-BOL-GALVANI2`, using `EU-13B`'s grid partitioner,
per-storey conservation fix and >8/floor cap (not the pre-EU-13B strip cutter Bologna had never
even reached, since it never had side-cars before this task).

| Metric | Value |
|---|---|
| Side-cars emitted | 1,204 / 1,204 simulated buildings (0 before this task) |
| `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` | 1,061 |
| `FALLBACK_PENDING_LAYOUT` | 143 (141 `NARROW_FOOTPRINT_LT_8M`, 2 `PARTITION_AUDIT_FAILED`) |
| `sources.json` manifest sha256 | `d274c142ed5f5212a31937c5f74d940253a63497adea93d26c66af7e6943fa4c` (matches the manifest on disk after this run) |
| `outputs_3D/` mirror | byte-identical (`diff -rq`, all four `eu_*` viewers and data folders) |

Acceptance (`tests/geometry/test_eu14b_bologna_layout_binding.py`, T02 subset, 4 passed):
one side-car per simulated building; every `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` side-car
conserves its declared `dwellings_total` exactly (distinct zone-name count); no storey exceeds the
ruled grid's 8-dwelling ceiling; pop-up header and `has_unconditioned_core` agree (`False` on all
1,204, per `D-EU-36` — the real-footprint layout never carves the MVP 4.3 unconditioned staircase
core, same as Madrid/Lyon/London).

🔴 **Finding, disclosed not hidden:** this `geometry_outcome` histogram (1,061 / 143) is the emitter's
post-hoc visualization layer, computed fresh under the new partitioner. It does **not** yet match
what Speed job `1295646` actually simulated (796 `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` / 408
`FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`, produced by `_geometry()`'s pre-EU-13B strip
cutter at `prepare()` time). The two only reconcile once `T05` rebuilds and resimulates. This is
the same gap `EU-13B` T08 disclosed for Madrid/Lyon/London before its own T09 closed it.

---

## 3. T03 — double-imputation disclosure

Every Bologna side-car now carries both provenance tags. Added
`construction_period_provenance` to the side-car dict (sourced from the row data `_it_rows`
already tags) and a matching `cprov` field into the viewer's per-building JS object
(`scripts/generate_eu_3d_viewers.py`), with a new `CONSTRUCTION PERIOD IMPUTED` pop-up badge in
the same visual style (`.m-badge.imputed`) as the existing `DWELLING LAYOUT EMITTED (IMPUTED
COUNT)` badge.

- 1,204 / 1,204 side-cars carry `construction_period_provenance ==
  IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` and a non-empty `dwelling_count_provenance`
  (`tests/geometry/test_eu14b_bologna_layout_binding.py`, T03 subset, 2 passed).
- Badge text `CONSTRUCTION PERIOD IMPUTED` and the field `"cprov":"IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD"`
  both present in the regenerated `eu_IT-BOL-GALVANI2_viewer.html` (1,204 embedded occurrences —
  one per building — confirmed directly, in addition to the test).
- Only Bologna currently sets `cprov`; the field is silently absent (`None`) for Madrid/Lyon/London,
  so their badge never renders — no other district is affected.

---

## 4. T04 — the fallback population and the 16, measured and named (stop-and-report point 2)

### 4.1 Reconciliation

| Source | Figure | Reconciles with |
|---|---|---|
| `summary_prerun.json` `population_attempted` | 1,220 | matches manifest population baseline |
| `summary_prerun.json` `population_prepared` | 1,204 | matches manifest row count |
| `summary_prerun.json` `blocker_exclusions` total | 16 (4 + 10 + 2) | `1220 - 1204 = 16` exactly |
| Post-T02 manifest `geometry_outcome` histogram | 1,061 emitted + 143 fallback = 1,204 | matches `population_prepared` exactly |

No discrepancy in either reconciliation.

🔴 **Finding, not closed:** the predecessor prompt's own §0 named "408" as the fallback population
needing this census, measured *before* T02 ran (`FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`,
under the pre-EU-13B strip cutter that actually ran in Speed job `1295646`). Running T02's corrected,
EU-13B-conforming partitioner dropped that population from 408 to 143 — the same direction and a
comparable magnitude to Lyon's narrow-footprint drop (30 → 2) under the same partitioner change.
The 408 and the 143 are not the same measurement: 408 is what was actually simulated; 143 is what
the new, not-yet-resimulated layout would produce. Per the task's own instruction ("any discrepancy
is a finding, not a rounding difference"), this is recorded here rather than silently reconciled.
The 143-row population below is the one carried forward, because it is the one `T05`'s
resimulation will actually run.

### 4.2 Census (a): the 143 buildings with no emitted layout, per reason token

| Reason token | Count | What datum is missing | Source that could supply it |
|---|---:|---|---|
| `NARROW_FOOTPRINT_LT_8M` | 141 | Nothing missing — a real geometric property of the footprint (its minimum-rotated-rectangle width is below the ruled grid's minimum module width). Not a data gap. | None; would require a different partitioning scheme for sub-8 m plates, which is a partitioner-design decision, not a data acquisition. |
| `PARTITION_AUDIT_FAILED` | 2 | Nothing missing — the emitted partition's area-conservation audit failed for these two specific footprints (an edge case in the regularized geometry). Not a data gap. | None identified; would need case-by-case geometric investigation, out of this task's scope. |

Both reasons are geometric limits of the ruled partitioner on real footprints, not missing input
data — no dwelling count was ever in question for these 143; their `dwelling_count_provenance` is
still computed and recorded, only the interior partition could not be emitted. **No dwelling count
was invented to move any of these 143 out of fallback.**

### 4.3 Census (b): the 16 buildings excluded pre-run

| Reason token | Count | What datum is missing | Source that could supply it |
|---|---:|---|---|
| `CENSUS_SECTION_NO_RESIDENTIAL_BUILDINGS` | 4 | A residential-building count for these 4 buildings' ISTAT 2011 census section (all `E8`-`E16` bins are zero in that section). | A newer ISTAT census (2021) for the same section, or the comune's per-building cadastral registry, if one exists and is accessible. |
| `CENSUS_SECTION_PERIOD_TIE_E8_E9` | 10 | The individual building's real construction year — the section-level tie between the `E8` and `E9` bins is a genuine ambiguity in the aggregate, not resolvable from the section alone. | A per-building age record (comune anagrafica catastale) for these 10, if it exists. |
| `CENSUS_SECTION_PERIOD_TIE_E9_E10` | 2 | Same as above, tied between `E9` and `E10`. | Same as above. |

🔴 A tie between two ISTAT bands is a real ambiguity, not a rounding problem. **No tie-break is
proposed or executed here.** If the owner judges one defensible, it is their ruling to make; this
document does not recommend a specific tie-break rule, only that a per-building age record — if
one can be sourced — would resolve it without guessing.

---

## 5. T05 — resimulation on Speed (stop-and-report point 3, `D-EU-38`)

Unblocked 2026-08-30. Rebuilt Bologna's IDFs from the T01-T03 layout-binding fix via
`scripts/run_eu_s2_district_campaign.py`'s existing `prepare()` — it already dispatches
`IT-BOL-GALVANI2` to `_it_rows` correctly (this task's T01 bug was in the side-car emitter only,
never in `prepare()`), and already calls `generate_european_building_dwelling_layout` (D-EU-33
parity), so no geometry code changed in this section.

### 5.1 IDF assembly: same residual as Madrid/Lyon/London

Rebuilding hit the same `EU-13B` T09 residual: 3 of 1,204 buildings failed
`IDF_ASSEMBLY_FAILED_ZeroDivisionError` (geomeppy's `intersect_match` on a degenerate zero-length
normal, not always reroutable even after `openubem/idf/surfaces.py`'s existing safety net) — 0.25%,
the smallest relative residual of the four districts (Madrid 0.94%, Lyon 4.7%, London 2.4%).
`population_prepared` dropped 1,204→1,201. Their 3 orphaned side-car JSONs (building_ids `32165`,
`32306`, `32468`) were removed since they no longer describe a simulated building.

### 5.2 Speed submission and harvest

Remote fleet dir `/speed-scratch/o_iseri/fleets/EU11_IT-BOL-GALVANI2` was cleared before shipping
(`rm -rf`, login-node-only) — a first ship attempt without clearing it left 3 stale D-EU-35-era
IDFs alongside the 1,201 new ones (remote count 1,204 vs expected 1,201), caught by
`ship_eu11_fleet.sh`'s own count assertion before anything was submitted. Shipped clean on the
second attempt (1,201/1,201). Submitted `sbatch --array=1-1201%16` from `speed-submit2` only,
fire-and-forget (job `1298672`), polled to completion with the `_ssh()`-wrapper pattern, never
`srun`, never login-node compute.

Harvested with `scripts/cluster/harvest_eu11_district.py` (`DISTRICT_JOBS["IT-BOL-GALVANI2"]`
updated to `1298672`). This surfaced and fixed a second bug: `parse_task()` crashed with
`TypeError: boolean value of NA is ambiguous` on the first task with no `task.rc` (15 of Bologna's
1,201 tasks — EnergyPlus hit the same pre-registered `GetSurfaceData` RoofCeiling vertex-mismatch
fatal as Madrid/Lyon/London, and the remote-deployed `submit_fleet_t08.sbatch` lacks the local
repo's `set +e`/`set -e` guard, so its `task.rc`-writing line never runs). Fixed at
`scripts/cluster/harvest_eu11_district.py:186`; confirmed non-contaminating by re-harvesting
against a freshly cleared local cache and getting an identical `pooled_eui_kwh_m2` both times.
Also discovered (not fixed, cosmetic-only, `[OPEN]`): the same remote script never writes
`platform.txt`/`energyplus_version.txt` at all, so Bologna's `platform_observed` /
`energyplus_version_observed` are now honestly empty rather than the misleadingly stale
2026-08-28 values every prior harvest silently carried forward. Both registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`, chapter "European locations EU-14B".

Speed result: 1,201 tasks run, 1,184 success, 17 `EPLUS_FATAL` (all missing `task.rc`, all the
`GetSurfaceData` fatal in every sampled case — same symptom class as Madrid/Lyon/London, not a new
defect; `heating_kwh`/`eui_kwh_m2` blank for these 17, never fabricated).

### 5.3 Re-emission after harvest

`harvest_district()` rewrites the manifest CSV from a fixed column list that does not include
`layout_json`, and recomputes `geometry_outcome` from `prepared_buildings.csv`'s
`_geometry()`-labelled value (`FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`, not the emitter's
own `FALLBACK_PENDING_LAYOUT`) — so T02's emitter was re-run once more, through the same T01 safety
path, against the freshly harvested 1,201-row manifest, to restore `layout_json` and the emitter's
own outcome labelling (matching the convention already visible in Madrid's post-`EU-13B`-T09
manifest). No new side-cars needed regenerating in substance (same deterministic partitioner, same
footprints) — 1,201 side-cars now on disk, one per manifest row.

### 5.4 Pooled EUI, before / after, and the `FINDING 199` verdict

| | before (`EU-14`/`D-EU-34`, job `1295646`) | after (`EU-14B` T05, job `1298672`) | delta |
|---|---:|---:|---:|
| Pooled heating EUI | 55.5346 kWh/m² | **47.4921 kWh/m²** | -8.0425 (-14.5%) |
| Pooled floor area | 2,520,390.9432 m² | 2,479,443.7385 m² | -40,947.2 m² |
| Population run / success | 1,204 / 1,202 | 1,201 / 1,184 | -3 / -18 |
| `geometry_outcome` (dwelling-partitioned) | 796/1,204 (66.1%) | 1,058/1,201 (88.1%) | +22.0 pt |

🔴 Both figures carry `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD`
on 100% of rows.

`FINDING 199`'s verdict **did not move toward CONSISTENT — it deepened.** `DR16`'s pre-registered
bands are CONSISTENT 115.0-165.0, WORTH INVESTIGATING (Low) 95.0-114.9, INCOMPATIBLE (Too Low)
<95.0. The pre-T05 figure (55.5346) was already inside INCOMPATIBLE (Too Low); the post-T05 figure
(47.4921) is *further* below the 95.0 floor, not closer to it, despite dwelling-partitioned
coverage rising from 66.1% to 88.1% under the same fix that pushed Madrid up and London across its
own CONSISTENT ceiling. Per `D-EU-38`'s own framing, this is a campaign-wide question (all four
districts sit 55-79% below or across their own dossiers' expectations), not Bologna's to answer
alone, and DR16's own recommended audit (HVAC setpoints, internal gains, boundary surface types) is
explicitly not attempted here. **No input was tuned to move this figure into a band.**

`docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_IT-BOL-GALVANI2_viewer.html` regenerated from
the harvest, mirror verified byte-identical (`diff -rq`, viewer HTML and full data directory).
`RESULTS_EU-11.md` updated: Bologna's figure, `geometry_outcome` split, Speed-failure census,
`FINDING 199`, and the DR12-16 table row all superseded, prior `EU-14`/`D-EU-34` state kept as a
labelled historical paragraph (same pattern `EU-13B` T09 used for Madrid/Lyon/London).

---

## 6. Deliverables checklist

- [x] `openubem/outputs/eu_evidence/EU-14B/RESULTS_EU-14B.md` (this document).
- [x] Bologna side-cars regenerated (1,201 post-T05; 1,204 through T02/T03), viewers regenerated
      (all four), `outputs_3D/` mirror byte-identical.
- [x] `walkthrough_progress_log.csv` — one row per task (T01-T05).
- [x] `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` — "European locations EU-14B" chapter:
      T01's manifest-corruption root cause, T05's harvest `NA`-comparison crash fix, and the
      `[OPEN]` remote-sbatch-script version-drift finding.
