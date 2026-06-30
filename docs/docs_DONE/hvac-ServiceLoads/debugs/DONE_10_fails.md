# INVESTIGATION & REMEDIATION — Phase-E: the 10 dropped buildings

- **Slug:** `phaseE-10-fails`
- **Date:** 2026-06-27
- **Author:** Manager (Opus session)
- **Status:** RESOLVED — PLAN APPROVED (2026-06-27). Group B (4 false drops) **RECOVERED**. Group A (6 geometry fatals) root cause **CORRECTED** (the §2.4 "split-surface / unrecoverable" claim is wrong — see the §2.4 correction banner) and the fix **PROVEN**: orient + thermal-mass fallback recovers them. User decision: **recover all 6 → 8,160/8,160**; execution plan in `10_fails_solution.md` §7A (T13 → T06-R → merge → figures → report).
- **Scope:** the 10 buildings (of 8,160) that did not produce a success row in `REPORT_phaseE_final.md` §4, and the §5 "la_rural OSM vertex winding" defect.
- **Evidence base:** the Phase-E temp work-tree survived at
  `C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseE\<cell>\` — every `eplusout.err`,
  `eplusout.sql`, `03_idf_manifest.parquet`, `04_simulation_manifest.parquet`,
  `01_buildings.gpkg`, and `repair/`/`reroute_fleet.lst` for the failures is intact and was read directly.

> **Headline:** Of the 10 drops, **only 6 are genuine EnergyPlus failures** (one geometry bug, not five-plus-one) and **4 are false drops** — buildings that simulated cleanly in EnergyPlus and were thrown away on a stale-bookkeeping mismatch. The 4 false drops have been **recovered** (T01+T02+T05, no resim needed). The 6 genuine failures have a **secondary structural geometry failure** (split interzone surfaces from `intersect_match`) that prevents recovery even after the orient fix eliminates the volume clamp. Fleet is currently **8,154 / 8,160**.

---

## 1. The 10 buildings — ground truth

Pulled from each cell's `05_results.csv` (`simulation_status` column) cross-referenced with the
`04_simulation_manifest.parquet` (EnergyPlus exit status) and the per-building `eplusout.err`.

| # | cell | osm_id | archetype | results status | E+ exit (manifest) | n_severe | TRUE cause |
|---|------|--------|-----------|----------------|--------------------|---------:|------------|
| 1 | la_rural   | way/472960972 | Warehouse | not_simulated        | **failed (fatal)** | 4  | Geometry — neg-volume clamp (A) |
| 2 | la_rural   | way/472961034 | Warehouse | not_simulated        | **failed (fatal)** | 7  | Geometry — neg-volume clamp (A) |
| 3 | la_rural   | way/472961088 | Warehouse | not_simulated        | **failed (fatal)** | 4  | Geometry — neg-volume clamp (A) |
| 4 | la_rural   | way/472961091 | Warehouse | not_simulated        | **failed (fatal)** | 12 | Geometry — neg-volume clamp (A) |
| 5 | la_rural   | way/472961171 | Warehouse | not_simulated        | **failed (fatal)** | 4  | Geometry — neg-volume clamp (A) |
| 6 | la_urban   | way/402215469 | Warehouse | failed               | **failed (fatal)** | 24 | Geometry — neg-volume clamp (A) |
| 7 | nyc_centre | way/266149332 | FullServiceRestaurant | failed_zone_mismatch | **success** | 0 | Stale `num_zones` — FALSE DROP (B) |
| 8 | la_centre  | way/319507579 | PrimarySchool         | failed_zone_mismatch | **success** | 0 | Stale `num_zones` — FALSE DROP (B) |
| 9 | la_rural   | way/472961047 | Warehouse             | failed_zone_mismatch | **success** | 0 | Stale `num_zones` — FALSE DROP (B) |
| 10| la_rural   | way/472961092 | Warehouse             | failed_zone_mismatch | **success** | 0 | Stale `num_zones` — FALSE DROP (B) |

Two causes only:
- **Cause A (geometry, genuine fatal): rows 1–6 (6 buildings).** All 6 are the *only* fatal `.err`
  files in the entire 12-cell fleet (verified: `grep -l Fatal` across all `sim_out/` → la_rural 5, la_urban 1, everything else 0).
- **Cause B (stale `num_zones`, false drop): rows 7–10 (4 buildings).** EnergyPlus returned
  `success` with `n_severe = 0`; the SQL holds valid, fully-resolvable results.

### Corrections this investigation forces onto `REPORT_phaseE_final.md`

| Report location | Report says | Truth |
|---|---|---|
| §4 fleet table | "Zone-mismatch parse failures: 3 (nyc_centre ×1, la_centre ×1, la_rural ×2)" | **4**, not 3 (the list of 4 is right; the count "3" is a typo) |
| §5 title + body | "la_rural OSM vertex winding … 5 buildings share the same OSM footprint defect … a single area of Lancaster digitised with a consistent winding-order error" | The negative-volume artefact is **fleet-wide, not localised**. *Every* la_rural building (and ~95% of la_urban per the report's own §10-pt-3) carries the same inverted-geometry clamp. The 5 fatal because they are the **largest**, not because their OSM winding is uniquely wrong. |
| §5 body | "there is no in-pipeline remedy without manual geometry intervention" | **False.** A one-line `shapely.orient` normalisation at the footprint stage is a clean in-pipeline fix (Cause A §2). No OSM re-digitising needed. |
| §12 #6 | la_urban way/402215469 = "degenerate geometry"; counts it separately from the "5 OSM-vertex" drops | It is the **same** inverted-geometry fatal as the la_rural 5 (identical `eplusout.err` chain). So it is 6 buildings, one bug — not "5 + 1 different". |
| §10 #3 | volume clamping is "benign … not a discriminator for pathological buildings" | True for small buildings, **but the clamp is the proximate cause of all 6 fatals** — for a large building the 10 m³ stand-in is what makes the heat balance diverge. "Benign" must be qualified by floor area. |

Net fleet integrity: **8,150 success → 8,154 ACHIEVED (Group B recovered 2026-06-27, no resim) → 8,160 BLOCKED** (Group A: orient fix eliminates volume clamp but a secondary split-surface heat-balance divergence prevents clean simulation; see §2.4 update). Current unrecoverable count = **6** pending manager decision.

---

## 2. Cause A — inverted geometry → negative zone volume → 10 m³ clamp → heat-balance fatal

### 2.1 The failure chain (from the surviving `eplusout.err`)

For all 6 fatal buildings the error file shows the identical sequence (example, la_urban/way_402215469):

```
** Warning ** GetVertices: Floor is upside down! Tilt angle=[0.0], should be near 180,
              Surface="BLOCK WAY/402215469_WHOLE STOREY 0 FLOOR 0001", Zone="WAY/402215469_F0_WHOLE".
** Warning ** Indicated Zone Volume <= 0.0 for Zone=WAY/402215469_F0_WHOLE
**   ~~~   ** The calculated Zone Volume was=-1376.24
**   ~~~   ** The simulation will continue with the Zone Volume set to 10.0 m3.
   ... (warmup) surface temperatures grow to Max=+238 C / Min=-280.9 C ...
** EnergyPlus Terminated--Fatal Error Detected.
```

### 2.2 Why it is **not** "5 clockwise OSM footprints"

Read directly from `01_buildings.gpkg` (EPSG:32611, projected metres) and `eplusout.err` of every la_rural building:

1. **The exterior winding is clockwise for *every* la_rural building** — the 7 cluster buildings
   *and* the healthy neighbours (shoelace sign identical). Raw winding does not separate fatal from healthy.
2. **Negative zone volume is universal in the cell.** A scan of all 147 la_rural `eplusout.err`
   files: every single one reports `Zone Volume <= 0.0 … set to 10.0 m3` (firstvol −35 to −26,184).
   The 141 "ok" buildings are *also* clamped to 10 m³ — they just survive it. This matches the
   report's own §10-pt-3 prevalence scan (587/617 la_urban buildings clamped, incl. healthy MidriseApartments).
3. **What separates the 6 fatals is size, not winding.** The clamped volume is always 10 m³; the
   *true* volume the clamp replaces scales with floor area. Fatal firstvol magnitudes: −1,631 / −1,815 /
   −1,581 / −3,987 / −26,184 (la_rural) and −1,376 (la_urban, a 1,173 m² warehouse). Surviving
   buildings sit mostly in the tens-to-hundreds. Once a large-floor-area, high-load building is
   forced into a 10 m³ air node, the air heat capacitance is ~100–1000× too small, warm-up
   temperatures diverge, and E+ terminates. The two cluster warehouses that did **not** fatal
   (way/472961047 = 758 m², way/472961092 = 612 m²) are simply small enough to tolerate the clamp.

**Therefore the true Cause A is:** the geometry pipeline emits zones whose surface normals are
oriented so that EnergyPlus computes a **negative** zone volume; E+ clamps every such zone to 10 m³;
for the handful of largest buildings the clamp itself drives the heat-balance fatal.

### 2.3 Where the orientation is (not) handled in the code

- `openubem/geometry/footprint.py` — `simplify_footprint` (L24–43) and `translate_to_origin`
  (L52–55) **never normalise winding**. There is no `shapely.orient` anywhere in
  `geometry/` or `idf/`. Footprints reach geomeppy in whatever order OSM stored them.
- `openubem/idf/surfaces.py` — `_has_negative_signed_area` (L224) *detects* an inverted
  core/perim floor, but its only response is to **reroute to one_zone_per_floor**
  (`_force_reroute_coreperim_to_one_zone_per_floor`, L507). Rerouting changes the *zoning*, not the
  *winding* — the per-floor WHOLE floors are still inverted, so the clamp persists. This is exactly
  why all 7 la_rural cluster buildings were rerouted (see `reroute_fleet.lst`) and 5 still fatal'd.
- The reroute is the wrong remedy for an orientation bug. The orientation must be fixed at the
  footprint, before extrusion, so geomeppy builds outward-consistent normals and a positive volume.

### 2.4 Proposed fix (Cause A) — EXECUTED 2026-06-27, secondary failure found

> ⚠️ **CORRECTION 2026-06-27 (manager): the "secondary structural geomeppy / split-surface
> (`FLOOR 0001_1`) / structurally unrecoverable" conclusion below is WRONG.** The interzone
> Ceiling↔Floor pairs are valid (matching 14-vertex, coincident, opposite winding). The real
> stage-2 blocker is a **thermal** failure — the all-`MATERIAL:NOMASS` envelope cannot damp
> top-zone solar gains → surface heat balance diverges. It is **fixable in-pipeline** with a
> targeted thermal-mass construction fallback, proven on the 2 hardest of the 6 (both zoning
> strategies). See `10_fails_solution.md` **§7A** for the corrected root cause, evidence, and the
> recovery plan. Group A is **RECOVERABLE** (user decision 2026-06-27: recover all 6 → 8,160/8,160).

**Orient fix applied (T01):** `shapely.geometry.polygon.orient(poly_local, sign=1.0)` inserted in
`openubem/idf/builder.py` immediately before `build_zones`. Result: **zero `Zone Volume <= 0`
warnings** for all 6 Group A buildings after fix. Direction was correct (CCW → positive volume).
Healthy large building (la_urban LargeOffice 10,330 m²) continues to `success`. The orient fix is
confirmed correct and kept.

**Secondary failure discovered (CP-1 blocker):** Despite positive volumes, all 6 fatals still
exit with temperature out-of-bounds / heat-balance divergence. The blocking error pattern:

```
** Severe  ** CalcHeatBalanceOutsideSurf: ZONE=..._PERIM[...] has an outside boundary condition of:
             ... Surface=..._FLOOR 0001_1 ...
** EnergyPlus Terminated--Fatal Error Detected.
```

`FLOOR 0001_1` is a **split interzone surface** produced by `intersect_match()` (geomeppy) when
two zones share a floor/ceiling boundary that geomeppy subdivides into sub-polygons. The
`_pair_interfloor_surfaces` function (surfaces.py L60) only pairs exact-vertex-match surfaces;
split surfaces have no valid counterpart in the adjacent zone's boundary condition, leaving an
unbalanced heat-flux → temperature divergence.

**Key finding: the secondary issue is pre-existing.** Grepping the original fleet's repaired IDF
`repair/way_472961091.idf` shows `FLOOR 0001_1` is **already present** there — the volume clamp
fatal was triggering first and masking this deeper issue. Forcing `one_zone_per_floor` (which the
original fleet reroute used) also fails: 76 severe errors, temperature divergence in WHOLE-floor zones.

**Experiments run (all with orient fix active):**
- la_rural/472961091 free-zoning → core-perim, 27 zones, severe=12, fail_fatal
- la_rural/472961091 forced one_zone_per_floor → 3 zones, severe=76, fail_fatal
- la_urban/402215469 → one_zone_per_floor (6 floors), severe=20, fail_fatal
- All 5 la_rural fatals free-zoning → 27–57 zones, severe=10–24, all fail_fatal

**Conclusion:** the 6 Group A buildings have a structural geomeppy incompatibility with their
specific polygon shapes (large irregular footprints → `intersect_match` splits → unpaired boundary
conditions). This cannot be fixed by orient alone or by zoning strategy switching.
Manager must decide: accept 8,154/8,160, pursue IDF-level surgery, or alternate approach.

---

## 3. Cause B — stale `num_zones` → parser false-drops a clean simulation

### 3.1 What the parser checks

`openubem/results/parser.py::_check_zone_integrity` (L187–232) counts the zones it can resolve
from the SQL (via the "Zone Lights Electricity Energy" keys → `ZONE_RX`) and **requires exact
equality** with `num_zones` from the manifest (L225):

```python
if len(resolved_zone_ids) != num_zones:
    return "failed_zone_mismatch", f"zone count mismatch: found {len(resolved_zone_ids)}, manifest says {num_zones}"
```

### 3.2 Why the count is stale (proven from on-disk artefacts)

For all 4 false-drop buildings, `03_idf_manifest.parquet` records `zoning_strategy = perimeter_core`
and a large `num_zones`, but the **simulated SQL** holds a one-zone-per-floor layout:

| building | manifest `num_zones` | manifest strategy | SQL zones (actual) | regex-resolved | E+ exit |
|---|---:|---|---|---:|---|
| nyc_centre way/266149332 (FSR) | 60 | perimeter_core | 12 × `..._F{i}_WHOLE` | 12/12 | success |
| la_centre way/319507579 (PrimarySchool) | 338 | perimeter_core | 13 × `..._F{i}_WHOLE` | 13/13 | success |
| la_rural way/472961047 (Warehouse) | 18 | perimeter_core | 2 × `..._F{i}_WHOLE` | 2/2 | success |
| la_rural way/472961092 (Warehouse) | 18 | perimeter_core | 2 × `..._F{i}_WHOLE` | 2/2 | success |

The SQL zone names are pure `_F{i}_WHOLE` (one_zone_per_floor) and the parser regex resolves **100%**
of them — there is no parsing problem and no foreign-osm_id (I2) problem. The found counts equal the
floor counts (12, 13, 2, 2). The manifest's 60/338/18 are the **pre-reroute core/perim** counts
(geomeppy core/perim ≈ (n_edges+1) zones per floor: FSR 5×12, school 26×13, warehouse 9×2).

### 3.3 Why the manifest was never corrected

The reroute that produced the WHOLE-zone IDFs is the **harness** repair pass, not the builder:
`scripts/validation/v12_cell_pipeline.py::verify_and_repair` (L405). Its second pass (L495–557)
forces one_zone_per_floor by monkey-patching `decide_zoning_strategy` (L520), **regenerates the IDF**,
re-ships and re-simulates — and the regeneration *does* return a corrected `num_zones`
(`builder.py:380 num_zones = len(extruded_zones)`). But the harness consumes only
`result["idf_path"]` (L526) and **never writes the corrected `num_zones` back into
`03_idf_manifest.parquet`**. Step 5 then reads the stale 60/338/18 and false-drops.

Confirmed by `reroute_fleet.lst`: la_centre = {319507579}, nyc_centre = {266149332},
la_rural = {all 7 cluster ways}. Every false-drop building is on a reroute list.

### 3.4 Proposed fix (Cause B)

Two independent fixes; do **both** (defence in depth), neither needs re-simulation:

1. **Bookkeeping (root cause):** in `verify_and_repair`, after a successful reroute, write the
   regenerated `result["num_zones"]` (and `zoning_strategy = "one_zone_per_floor"`) back into the
   row of `03_idf_manifest.parquet` for that osm_id, before Step 5 runs.
2. **Parser robustness (belt-and-braces):** in `_check_zone_integrity`, relax the hard equality.
   The genuine safety gate is the **foreign-osm_id (I2) check**, which already raises. The exact
   zone-count equality is too brittle across reroutes. Options, in order of preference:
   - accept when every resolved zone belongs to the building and `resolved ≥ 1`, demoting the count
     mismatch to a `data_quality_flag` (e.g. `ZONE_COUNT_REROUTED`) rather than a drop; **or**
   - compare against the **actual IDF** zone count at parse time instead of the manifest; **or**
   - keep the check but treat "found < manifest with all-resolved, no-foreign" as success.

**Recovery of the 4 today (no resim):** the valid SQL already exists in the temp work-tree. Re-running
Step 5 parse for these 4 cells against the existing `eplusout.sql` with either fix applied recovers
all 4 success rows immediately → 8,150 → 8,154.

---

## 4. Remediation task list (for a fresh executor)

> Binding contract: this document + `REPORT_phaseE_final.md`. Stay in cwd. No plan-writing, no scope
> creep. Stop-and-ask on any spec ambiguity. Default to no comments. **Do not change model results
> or the report's adopted numbers without manager sign-off** — Phase-E is the adopted baseline.

**Track B — ✅ COMPLETE 2026-06-27:**

- **T01 ✅** — `openubem/results/parser.py` `_check_zone_integrity` relaxed: keeps I2 foreign-osm_id
  raise; zero-resolved-zone drop kept; pure count-shortfall (resolved ≥ 1, no foreign) → non-drop.
- **T02 ✅** — `openubem/idf/builder.py` orient chokepoint added (`shapely.orient(sign=1.0)` before
  `build_zones`). Healthy buildings unaffected.
- **T05 ✅** — All 4 Group B buildings parsed from existing SQL (no resim):
  EUI 873.2 / 185.2 / 19.8 / 20.2 kWh/m², all `parse_status=success`.
- **Merge (T07), Figures (T08–T10), Report (T12)** — pending Group A resolution.

**Track A — ⛔ BLOCKED at CP-1:**

- **T04 ✅ (orient gate, partial)** — orient fix direction CORRECT (all volumes now positive,
  0 `Zone Volume <= 0` warnings); healthy building stays success. **BUT all 6 fatals still
  `failed_fatal`** with secondary split-surface heat-balance divergence (see §2.4 update).
  Per solution plan §1.7 hard rule: executor stopped and escalated to manager.
- **T06–T09 on hold** pending manager decision.

---

## 5. Decisions for the user (manager-of-manager)

1. **Track B (recover the 4 false drops)** — ✅ **DONE** (2026-06-27). Fleet is now 8,154/8,160.
2. **Track A (Group A, 6 geometry fatals)** — ⛔ **AWAITING DECISION.** Orient fix eliminates the
   volume clamp (correct direction, confirmed by experiment) but a secondary split-surface heat-balance
   failure blocks all 6. Three options for the manager:
   - **Option 1 (accept 8,154/8,160):** Group A structurally unrecoverable without deeper IDF surgery.
     Proceed to merge T07 + figures T08–T10 + report T12 with 8,154 as the final fleet count.
   - **Option 2 (IDF-level surgery):** Patch `intersect_match` surface pairing or pre-repair the split
     surfaces in the repaired IDFs before re-simulation. Complex, out of plan scope.
   - **Option 3 (alternative geometry):** Generate these 6 buildings with a bounding-box fallback
     (`fallback_bbox`) to avoid `intersect_match` entirely, at the cost of approximate geometry.
3. **Report status** — §4/§5/§10/§12 corrections depend on Track A decision. Report update (T12)
   deferred until that decision is made. Manager to action.

---

## 6. Evidence index (all under the surviving temp work-tree)

- Fatal error chains: `…\phaseE\la_rural\sim_out\way_4729609*\eplusout.err`,
  `…\phaseE\la_urban\sim_out\way_402215469\eplusout.err`
- Universal negative-volume scan: all 147 `…\phaseE\la_rural\sim_out\way_*\eplusout.err`
- Stale-count proof: `…\phaseE\<cell>\step3\03_idf_manifest.parquet` vs
  `…\phaseE\<cell>\sim_out\way_*\eplusout.sql` (`Zones` table)
- Reroute provenance: `…\phaseE\<cell>\step3\reroute_fleet.lst`, `…\repair_fleet.lst`, `…\step3\repair\*.idf`
- Source: `openubem/geometry/footprint.py` (no orient), `openubem/idf/surfaces.py:224,507`,
  `openubem/idf/builder.py:380`, `openubem/results/parser.py:187-232`,
  `scripts/validation/v12_cell_pipeline.py:405,495-557`
</content>
</invoke>
