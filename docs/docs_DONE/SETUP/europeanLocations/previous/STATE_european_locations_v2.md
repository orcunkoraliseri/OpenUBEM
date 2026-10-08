# European locations × Step 8 — arc state (v2)

**Opened:** 2026-08-28. **Supersedes as the read-first document:** `previous/MVP_european_locations.md`
(2,761 lines) and `previous/WALKTHROUGH_european_locations.md` (1,591 lines), both **FROZEN on 2026-08-28
and no longer appended to**. They remain the authority on how each fact was obtained — every ruling,
finding, gate table, caveat list and acceptance record stays there, unchanged. Nothing was rewritten in
the move.

**This document carries current truth only.** If a fact is not here, it is either history (see the frozen
docs) or it has not been established. Keep it short: when an entry stops being current, replace it, do
not append below it.

---

## 1. What may be quoted, and what may not

🔴 **The quotable perimeter is the 149 marker-free certified cells** — `uk` 75, `it` 74, **`es` 0** —
of the 510-cell campaign, ruled `D-EU-28` Option B. The five-`f` set is **15 pairs** (`uk` 8, `it` 7).
Certification is a conjunction: three bitwise-identical `heating_kwh` **and** `severe_count = 0` **and**
`fatal_count = 0` **and** all three replicates `completed`. **Never quote the 510, the 395, the 249, the
191, the 136 or any raw `completed` count as a perimeter.**

| Bar | Ruling | What it forbids |
|---|---|---|
| **`es` is never quotable, at any level** | `D-EU-28` / `FINDING 182` | All 42 `es` certified cells carry `marker_psy` in all three replicates; the marker is perfectly confounded with the fold |
| **`uk` is never quotable at fold level** | `D-EU-26` Option B | `uk` loses 17 of its 36 archetypes to the fail-closed `Wall_1` host check — 47 % of the fold |
| **`it` is the only fold-level figure** | above, jointly | **108.25 kWh/m² ± 0.16 % re-run tolerance** area-pooled heating EUI. **The tolerance is mandatory wherever the figure appears**, and is itself stated as measured on **35 of the 74** cells (`FINDING 192`). ⚠ **The cell range 45.08–156.70 is WITHDRAWN** |
| **Heating-only EUI** | `EU-10`, `single_simulated_end_use_no_reconstruction` | Never compare it to a whole-building EUI or a measured total |
| **Annual claims are not supported** | `FINDING 184` | The `f` manipulation is mean-conserving **by construction** (`openubem/semantic/european_schedules.py:56`, asserted at `:60`); annual movement < 0.5 % against a 15–50 % literature expectation. **Peak and timing claims only** |
| **Radiant exchange is corrected, not modelled** | `D-EU-29` / `fixviewfactors` | The equivalent-envelope zone is unenclosed, so EnergyPlus completes the view-factor matrix itself. **State this wherever 108.25 kWh/m² appears** |
| **No `S3` result without its split** | `D-EU-25`, `D-EU-23` | **12 partitioned / 84 massing** of 96; quote `S3` over **1,255**, never over 1,724 |
| **`GEO-10`'s third rung is 31** | `GEO-10` scoring | Never "4 / 12 / 32 / 96" |
| **Bologna Aug–Nov** | `D-EU-19` | No monthly or seasonal `it` figure for Aug–Nov without restating the October exception |
| **The difference perimeter is 92, not 149** | `D-EU-30` Option A | An `f`-versus-baseline difference may be quoted only where the cell's own `f=0` control is perimeter-grade: **92 cells / 28 archetypes** (`it` 47, `uk` 45). **No difference claim for the other 29.** The **level** perimeter stays 149 — every `f`-difference statement must carry both numbers |
| **No `EU-11` S2 EUI without its zone over-count** | `FINDING 201` | The four district pooled EUIs (Madrid 79.0862, Lyon 70.0619, London 74.7151, Bologna 55.5346 kWh/m²) were all simulated with **more dwelling zones than the buildings declare** — 17,199 declared → 19,133 emitted, **+11.2 %**, over-emitting in **75.6 %** of buildings. Quotable only with that stated; **never** as a validated district EUI until `EU-13B` `T09` is ruled and run |
| **No cell-level number from the 149** | `D-EU-31` Option A | `FINDING 191`: **53 of 149** certified cells give more than one `heating_kwh` over ten re-runs; re-run risk on a single cell reaches **79 %**. No individual cell's value may be quoted, ranked, tabulated or used as an example. **Fold-level aggregates only** |

⚪ `heating_kwh` comes from the `Zone Ideal Loads Zone Total Heating Energy` **variable**
(`run_eu_s2_campaign.py:285`), never from a meter — no saved IDF carries an `Output:Meter`, which is why
`G8.10`/`G8.11` are **vacuous by construction and can never FAIL**.

---

## 2. Work packages

| WP | What it is | Status | Owner of what remains |
|---|---|---|---|
| **EU-01** | TABULA loader | Completed | — |
| **EU-02** | Semantic crosswalk, neighbourhood selection | Completed | — |
| **EU-03** | Envelope and internal-mass adapter | Completed | — |
| **EU-04** | Dwelling and core layout adapter | Completed | — |
| **EU-05** | Residential HVAC and ventilation adapter | Completed | — |
| **EU-06** | External occupancy schedule adapter | Completed | Upstream — `D-EU-09` (`f>0`) |
| **EU-07** | Actual-weather registry | Completed | — |
| **EU-08** | Campaign and SLURM wrapper | Completed | — |
| **EU-09** | Gates and mutation suite | Completed | — |
| **EU-10** | Results and dossier | Completed | — |
| **EU-11** | Full-district `S2` campaign — every residential building of the four districts, on Speed | Completed | — |
| **EU-11B** | Bind `EU-11` results into the four district 3D viewers | Completed | — |
| **EU-12** | Emit per-building dwelling layouts + click pop-up in the four viewers | Completed | — |
| **EU-13** | Extend dwelling-layout coverage from 51/4,186 toward full coverage (`D-EU-33`) | Completed | — |
| **EU-14** | Reopen Bologna construction-year — retry INSPIRE, else tagged imputation (`D-EU-34`) | Completed | — |
| **EU-13B** | Make the emitted dwelling layout the ruled MVP §4.2 scheme | Done 2026-08-30 (T01–T05, T07–T10); `T06` blocked | Owner — `D-EU-36` carve-vs-add still unruled; `FINDING 205` (London EUI moved CONSISTENT→WORTH INVESTIGATING); new: circulation polygons are computed but never drawn in the viewer, see investigation doc |
| **EU-14B** | Give Bologna dwelling layouts without corrupting its manifest | Done 2026-08-30 (T01–T05) | Owner — `FINDING 199` deepened, not resolved; campaign-wide `DR16` audit is a decision for the owner |

*The **What it is** column is the deliverable name from Table 9.7, nothing more. Status is one of
**Completed**, **In progress** or **Not started**, and nothing else. **This table carries no notes.** It is maintained from the append-only `content/walkthrough_progress_log.csv`; the evidence
behind each value is §3 below and, for anything older, the frozen documents.*

**All fourteen `EU-01`–`EU-14` work packages are Completed. Two new packages, `EU-13B` and `EU-14B`, were
opened 2026-08-28 on owner instruction** after the owner inspected the Madrid, Lyon and London viewers and
found the emitted floor layouts do not match the scheme this arc ruled. They are **plan-only in this
session**: the prompts exist, no code was written, execution is the owner's to dispatch. Detail, with the
four measurements behind them, is in §3.

- ✅ **EU-05 — CLOSED 2026-08-28 on owner instruction, with two stated exclusions.** 95/95 on four checks
  over the 95 accepted `S3` IDFs, plus the off-path meter sidecar (95/95 all five meters, hourly heating
  series identical, `max_abs_diff 0.0`, every promoted `idf_sha256` recomputed unchanged).
  ⚠ **Exclusion 1 — `meters_present` is 0 of 95 and stays so.** `write_outputs()` is still not wired into
  either campaign script; emitting meters in place would re-run the promoted campaign and change every
  hash, refused on the same ground as `D-EU-24`'s geometry remedy. **The closure does not repair this.**
  ⚠ **Exclusion 2 — the `core_unconditioned` pass is VACUOUS** (0 of 95 emit a core zone, by design) and
  must never be quoted as evidence.
- ✅ **EU-06 — CLOSED 2026-08-28 on owner instruction, at `f=0` only.** 95/95 on all five checks, 374
  distinct schedule CSVs, layout split matching the manifest.
  ⚠ **`f>0` is NOT closed and was never OpenUBEM's to close** — it is blocked upstream by `D-EU-09`, the
  Step 7 chaining rule. **Never read this closure as covering the injected-series path.**
  ⚠ "`People` assignment" is loose wording: 0 of 95 emit a `People` object — the gain is an
  `OtherEquipment`, deliberate and tested. Never read it as a missing-`People` defect.
- ✅ **EU-08 — CLOSED 2026-08-28 by GSSCanada 4J, from retained artefacts only**, with two measured
  coverage gaps stated rather than worked around, over 1,185 retained manifests (perimeter subset
  447/447 present). ⚠ **`dependency_digest` present in 0 of 1,185** — every replicate ran into a fresh
  root and no cache was ever consulted, so `G8.9` is VACUOUS at population 0 and perturbation **P02 is
  VACUOUS for the same reason**. ⚠ **`platform` present in 0 of 1,185** (`energyplus_version` present in
  all 1,185, as the legacy single string): every retained manifest predates the `platform` field, so
  `G8.14`'s identity arm PASSes 149/149 while **its platform arm is NOT SCOREABLE**. Manifests were not
  retrofitted. **No two-host claim is available from this campaign.**
- ✅ **EU-09 — CLOSED 2026-08-28, restated not re-scored: 8 PASS / 1 FAIL / 4 VACUOUS / 4 NOT SCOREABLE.**
  PASS `G8.5 G8.6 G8.8 G8.12 G8.13 G8.14 G8.15 G8.16`; FAIL `G8.0`, carried at 99/121 with the 29
  out-of-perimeter `f=0` controls stated, **never PASS**; VACUOUS `G8.7` `G8.9` `G8.10` `G8.11`, each at
  population 0 and each naming why; NOT SCOREABLE `G8.1`–`G8.4` per `D-EU-31`, **never PASS**.
  One verdict moved, and on an artefact rather than on argument: **`G8.15` FAIL → PASS 149/149**, because
  the `D-EU-29` Option A approval set `eu_approved_warning_kinds_v1.0.json` (`sha256 863c9e59…`,
  perimeter `campaign_149`) now exists — 4J re-derived it rather than accepting ours, 8 observed kinds
  exactly the 8 approved, none untriaged. That is also the single gate behind the earlier 12/1/4 vs
  11/2/4 disagreement. ⚠ `G8.5`/`G8.6` stay PASS deliberately — they are ±15 % / ≤1 h peak-band gates,
  **not bitwise tripwires**, and must never be cited against `FINDINGS 188`–`192`.
- ✅ **EU-10 — CLOSED 2026-08-28 under `D-EU-31`; the dossier was not recomputed, the barred fields stay
  on disk and stop being quoted.** Deleted from citation: **all 149 `cells[]` records** (every per-cell
  annual/monthly/peak heating and EUI); `eui_kwh_m2_min/_median/_max`, so the `it` cell range
  **45.08–156.70 is WITHDRAWN** and the cell median **113.09** goes with it; `all_perimeter_cells_informational`,
  i.e. **99.79 kWh/m²**, barred twice over as both cell-level and `uk`-crossing; and the
  15 `f_sweep.pairs[]` per-pair values. **Surviving quotable set: `it` = 108.25 kWh/m² ± 0.16 % re-run
  tolerance** (stated as measured on **35 of the 74** cells, numerically stable and **not** bitwise
  reproducible, never "re-measured"), heating-only; `uk` withheld at fold level; `es` not quotable at any
  level; 93.768 a two-end-use model total, never a whole-building EUI; every `f`-difference carrying both
  perimeters (92 cells / 28 archetypes for the difference, 149 for the level) and, per `FINDING 184`, a
  peak-and-timing claim only.
- ⚠ **What a closed `EU-05`/`EU-06` did NOT supply, raised by 4J rather than worked around.** `EU-05` is
  exactly why `G8.10`/`G8.11` are VACUOUS and **stay VACUOUS on this campaign**: `meters_present 0 of 95`
  appears on 4J's side as **0 `Output:Meter` objects in all 149 perimeter IDFs**, and the off-path meter
  sidecar is evidence about the `S3` population, **not about these 149 cells**, so it cannot fill the gap —
  recorded as permanent, not scheduled, and the VACUOUS `core_unconditioned` pass is cited nowhere.
  `EU-06`'s `f=0`-only closure is **not load-bearing** for 4J: their 121 `f>0` cells rest on their own
  driver and on the 10.1 chaining-closure notice's lift by reference, and they do not read our closure as
  covering the injected-series path.

---

## 3. Open items

✅ **`EU-11` — CLOSED 2026-08-28: simulate all four districts, every residential building, on Speed.**
Harvest done, results in `results/RESULTS_EU-11.md`; `EU-11B` viewer binding done, audited PASS in
`validation/VALIDATION_EU-11B_viewer_integration_2026-08-28.md`.

✅ **`EU-12` — CLOSED 2026-08-28: per-building dwelling-layout side-cars + click pop-up in the four
viewers.** 1,340 side-cars emitted (Madrid 961, Lyon 297, London 82, Bologna 0 — never simulated); 51
`DWELLING_LAYOUT_EMITTED` (all Madrid, 5.3% of Madrid's simulated stock), 1,289 massing-box fallback,
2,846 not simulated. `FINDING EU-12-01` (emitted layouts extrude storey 0 only, vs `n_storey` for the
massing-box path) and `FINDING EU-12-02` (emitted scheme is `equal_strip_long_axis`, not the MVP
point-block/corridor figure) are recorded in `openubem/outputs/eu_evidence/EU-12/RESULTS_EU-12.md`.
Audited PASS, pop-up draw path traced end-to-end (not just counted), in
`validation/VALIDATION_EU-12_dwelling_layout_popup_2026-08-28.md`. No live task remains in this arc.
Scope **4,186 residential buildings** — `ES-MAD-BERRUGUETE` 1,194, `FR-LYO-HAUTCOEURPENTES` 530,
`GB-LDN-STDUNSTANS` 1,242, `IT-BOL-GALVANI2` 1,220 — against the four pinned fold EPWs
(`es_madrid_2009_2010_y*`, `uk_london_2014_2015_y*`, `it_bologna_2013_2014_y*`, `fr_lyon_bron_2023_era5`,
all `RULED_PINNED_EXCEPTION` in `weather_registry.json`). This is the **`S2` real-footprint perimeter**,
not the S0 archetype campaign: it is a **new perimeter with its own gates**, and it neither extends nor
re-opens the frozen 149 — `D-EU-28`, `D-EU-30`, `D-EU-31` and the spent `D-EU-27` re-run budget are
untouched by it.

✅ **`EU-13` — CLOSED 2026-08-28: dwelling-layout coverage extended from 51/4,186 to 1,078/1,340 simulated.**
Owner ruling `D-EU-33` (`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-33_dwelling_layout_full_coverage_2026-08-28.md`)
implemented on all three mandatory fronts (executed externally via Gemini Antigravity, `RESULTS_EU-13.md`):
`FINDING EU-12-01` resolved (every storey stacked, not just storey 0); general multi-angle/radial partition
extended coverage to non-convex/courtyard footprints, 99.08% audit pass rate (1,078/1,088 non-narrow) without
loosening `audit_european_floor_partition`; 382 missing dwelling counts imputed via the four-tier cascade,
tagged `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`. `NARROW_FOOTPRINT_LT_8M` (183 Madrid, unchanged) stays a
massing box per `D-EU-33` §3.4. Coverage: Madrid 770/961, Lyon 239/297, London 69/82, Bologna 0/0 (untouched,
`EU-14`'s scope). 10 remaining non-narrow fallbacks individually named in `RESULTS_EU-13.md` §5.
🔴 **Post-delivery audit finding**: owner caught the pop-up claiming `Unconditioned core: Yes` on every
emitted building although zero core zone was ever emitted (real-footprint layouts never carve a core, by
design, per GEO-01) — `emit_eu11_layout_sidecars.py:183` had wired in an unrelated density flag from the
synthetic-TABULA allocator instead of the real layout's own (always-`False`) field. Fixed same day, side-cars
and viewers regenerated for all 4 districts (0 remaining false claims across 1,340 buildings), registered in
`OpenUBEM_debug_References.md` (European locations X-05 chapter). Coverage counts unaffected by the fix.
🟢 **Second, deeper post-delivery finding, `D-EU-35` RULED Option 1 and EXECUTED 2026-08-28**: EU-13's
`geometry_outcome` was recomputed independently of what actually ran on Speed —
`run_eu_s2_district_campaign.py:_geometry` (the function that built the real submitted IDFs) had the same
missing-`n_storey` bug plus no imputation cascade at all, so most of the ~1,077 newly-relabelled buildings
were actually simulated under older, simpler zoning; their published `heating_kwh`/`floor_area_m2`/
`eui_kwh_m2` did not match what the pop-up showed. Campaign script fixed; Madrid/Lyon/London IDFs
regenerated against the synchronized `prepare()`, resubmitted to Speed (jobs `1294465`/`1294513`/`1294581`),
and harvested — new pooled EUIs 79.0862/70.0619/74.7151 kWh/m², `geometry_outcome` now 80–84 %
dwelling-partitioned in all three (was 0–5 % pre-fix). Full write-up: `results/RESULTS_EU-11.md`. Bologna
untouched (0 buildings affected, resolved separately by `EU-14`). Ruling record:
`debugs/docs/DECISION_REQUEST_D-EU-35_geometry_simulation_desync_resimulation_2026-08-28.md`.
🔴 **`FINDING 198` (new)** — Lyon's resimulated EUI (70.0619, 80.5 % dwelling-partitioned) did not rise
toward DR14's own dwelling-partitioned reference mean the way a population-weighted blend predicts; barely
above the pre-fix, 100 %-fallback figure (64.6017). Not diagnosed; see `results/RESULTS_EU-11.md` Lyon
section and DR12–16 table.

🟡 **`EU-14` — OPENED 2026-08-28: reopen Bologna — retry INSPIRE, else a tagged, disclosed imputation.**
Owner ruled `D-EU-34` (`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-34_bologna_construction_year_relax_2026-08-28.md`):
`IT-BOL-GALVANI2` at 0/1,220 simulated is not an acceptable end state. Step 1 (mandatory): retry the Italian
INSPIRE Buildings WFS live — the investigation's four attempts all failed on transport grounds (DNS/404/500),
not a confirmed absent field. Step 2 (only if step 1 fails): impute each building's TABULA period from its
ISTAT 2011 census-section construction-period band by centroid join, tagged
`IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD`, never `OBSERVED_YEAR`, never merged into the same pooled figure
as the three observed-year districts without that tag stated. The investigation's own "Fail" disposition
(`debugs/EU11_Bologna_construction_year_investigation.md`) is not overturned, only layered on. Handed to the
external executor as `prompts/PROMPT_EU-14_bologna_construction_year_reopening.md`; INSPIRE WFS retry
(step 1) failed again, ISTAT census-section imputation (step 2) applied — 1,204/1,220 prepared (16
excluded). External executor stalled mid-run; taken over directly (owner instruction, 2026-08-28), job
`1295646` monitored to completion and harvested: 1,202/1,204 success, pooled EUI **55.5346 kWh/m²**
(796/1,204 dwelling-partitioned). 🔴 **`FINDING 199` (new)** — 55.5346 falls in DR16's own pre-registered
INCOMPATIBLE (Too Low) range (<95.0) for its asset-rating protocol (CONSISTENT 115.0–165.0); recorded, not
corrected — see `results/RESULTS_EU-11.md` Bologna section. `EU-14` is now **COMPLETE**. Its four
`PROMPT_EU-14` §6 deliverables were found missing on audit and closed out the same day: `RESULTS_EU-14.md`
written, `construction_period_provenance` added to `MANIFEST_COLUMNS` and backfilled
`IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on **1,204 of 1,204** Bologna rows, viewers regenerated so
`sources.json` matches, `fundamentals.md` §8.5 restated. Pooled EUI, area and `geometry_outcome` counts
verified unchanged across the column insert.

---

🟡 **`EU-13B` — OPENED 2026-08-28: the emitted dwelling layout is not the scheme this arc ruled.** The owner
inspected the Madrid, Lyon and London pop-ups and reported that the floor layouts look nothing like
`content/figure_4_2_dwelling_layout_schemes.svg` — no corridors, disorganised residential zones. Measured
the same day across all 1,340 side-cars and against the IDFs that actually ran on Speed, four findings, all
recorded rather than corrected:

🔴 **`FINDING 200` — the emitted scheme is not the ruled scheme, in 100 % of cases.** `scheme =
equal_strip_multi_angle_sweep` on **1,078 of 1,078** emitted layouts; `has_unconditioned_core = false` on
**1,078 of 1,078**. The ruled scheme (`MVP` §4.2/§4.3, and the method of record,
`IMP_step8/outputs/floor_layout_generation_report.md` §5–§9) is an `n_u × n_v` grid — `1×1`, `2×1`, `2×2`,
`3×2`, `4×2` — around a **centroidal unconditioned stair core of 12–25 m²**, with a **1.80 m double-loaded
corridor spine** for `L/W ≥ 2.0`, wing decomposition for L-shapes, and courtyard unfolding. None of that
exists on the real-footprint path; the footprint is cut into parallel strips. `FINDING EU-12-02` recorded
the same thing on 51 buildings in `EU-12`; `EU-13` then generalised the strip cutter to 1,078 rather than
implementing the scheme, so the gap grew by 21× instead of closing.

🔴 **`FINDING 201` — the declared dwelling total is not conserved, and the error is in the physics.**
`units_per_floor = ceil(total / storeys)` is applied to **every** storey
(`run_eu_s2_district_campaign.py:135`, `emit_eu11_layout_sidecars.py:122`), discarding the correct q/(q+1)
stratification that `allocate_european_dwellings` (`european_residential.py:715`) already computes and
asserts. **815 of 1,078 (75.6 %)** emitted layouts over-emit; **17,199 declared dwellings become 19,133
zones, +1,934 (+11.2 %)**. Verified in the simulated IDF, not only in the pop-up: `way/51781396` declares 69
dwellings and `GB-LDN-STDUNSTANS/idfs/0567d9cb0dc88410.idf` carries **85** distinct `_F*_dwelling_*` zone
names (+23.2 %). 🔴 **Every `EU-11` pooled EUI was produced under this over-count.**

🔴 **`FINDING 202` — dwellings per floor is uncapped.** The ruled grid table stops at `4×2` = 8 units per
floor; **62 of 1,078 (5.8 %)** emit more, reaching **32 per floor** (`relation/3730743`, 1,869 m²
cross-shaped plate) where the strips overlap into unreadable slivers.

🔴 **`FINDING 203` — Lyon's missing simulations are a ruled-table gap, not missing data.** The owner asked
why residential buildings with measured height and storeys show `not simulated`. `derive_bdtopo_building_type`
(`european_archetype_mapping.py:185`, the ruled `D-EU-04-G` Option G1 table) covers only
`1 dwelling / ≤4 storeys`, `2–12 / ≤4`, `≥15 / ≥5`; everything else is fail-closed. **226 of Lyon's 233
exclusions** are that gap (`TYPOLOGY_SIGNALS_DISAGREE` 189, `TYPOLOGY_DWELLINGS_IN_REGISTRY_GAP_13_14` 37)
against only **7** genuine missing-datum exclusions. A well-attributed 10-storey / 8-dwelling building has
no ruled type.

⚠ **Two owner decisions block the fix, and both are PROPOSED, not taken.**

- **`D-EU-36` — does a real footprint get an unconditioned circulation core?** Today it gets none, and that
  is deliberate, not an oversight: the `D-EU-01`/`GEO-01` area-conservation contract means a core can only
  be **carved** from the observed shell (shrinking conditioned area, moving every EUI denominator) or
  **added outside** it (making the building larger than its measured footprint —
  `generate_external_unconditioned_core`, `european_residential.py:377`, which refuses non-rectangular
  plates). ⚪ **Recommendation: carve, and republish the conditioned-area denominator alongside the gross
  footprint area for every building.** The core is the mechanism behind the party-wall buffering the MVP
  cites ($b_u = 0.50$–$0.80$, 30–50 % transmission moderation); a layout without it is not the ruled model.
  Adding area outside an observed footprint states something false about the district.
  🟢 **PARTLY RULED 2026-08-28 — the owner set a coverage bar and only a coverage bar: `≥ 95 %` of
  buildings is sufficient, 100 % is not required.** So `EU-13B` **fails closed on the residual** — a
  building the ruled grid cannot express keeps `one_zone_per_floor` and is counted in a disclosed residual,
  and is never forced into a grid that does not fit it. What the bar does **not** permit is reducing a
  building's dwelling count to make it fit, which is `FINDING 201` itself. 🔴 **Carve-versus-add is
  still open and `T06` stays blocked on it.** ⚪ The bar was measured before it was set, over the exact
  population `EU-13B` re-partitions (the 2,544 prepared for `S2`), geometry only, nothing simulated:
  **fleet 2,469 / 2,544 = 97.05 %**, against **1,874 / 2,544 = 73.7 %** emitted by the implementation
  today — so conforming to the ruled scheme *raises* coverage while fixing the count. Per district:
  Madrid 917 / 961 = 95.4 %, Lyon 284 / 297 = 95.6 %, Bologna 1,204 / 1,204 = 100 %, and 🔴 **London
  64 / 82 = 78.0 %, below the bar — the bar is a fleet bar, not a per-district one, and no London
  district-level result may be described as meeting it.** The only failure mode fleet-wide is the `> 8`
  per-storey refusal (75 buildings); there is no habitability failure and no area failure anywhere.
  Worked example, drawings and the executor's acceptance test:
  [`EXAMPLE_dwelling_layout_validation_2026-08-28.md`](EXAMPLE_dwelling_layout_validation_2026-08-28.md).
- 🔴 **`FINDING 204` — the two circulation criteria in MVP §4.3 conflict outside a narrow plate
  window, and the fleet is mostly outside it.** §4.3 states communal circulation as **6–12 % of gross
  floor area** *and* **12.0–25.0 m² per floor**; those hold together only for plates of **100.0–416.7 m²**.
  Measured on the 2,544 prepared: **1,602 (63.0 %) inside**, 542 plates too small, 400 too large. The
  conflict is structural, not marginal — §4.2 requires a 1.80 m double-loaded spine for `3×2`/`4×2`, and
  1.80 m across a 55 m plate is 99 m² whatever §4.3 says; on the eight-building sample the percentage rule
  holds everywhere (5.0–11.7 %) while the 25 m² ceiling is exceeded on five of seven, up to 97.91 m². The
  prototype let the percentage rule win and read 12.0–25.0 m² as descriptive of the Ankara plate sizes it
  was measured on (mean 18.4 m²). 🔴 **That is not this session's call:** `EU-13B` must tag every
  building where the absolute band was departed from, and the owner must rule which criterion binds.
- **`D-EU-37` — is the `D-EU-04-G` typology table extended to its uncovered regions?** Extending it would
  recover a large part of Lyon's 226 and, on the same rule, Madrid's 77 and London's 345
  `UNMAPPABLE_RESIDENTIAL_TYPE`. ⚪ **Recommendation: measure first** — `EU-13B` `T10` reports the joint
  `(dwellings, storeys)` distribution of the excluded, per district, before any band is widened. 🔴 No band
  is widened by an executor.

⚠ **A third call is the owner's alone: resimulation.** `EU-13B` `T01`–`T05` change zone counts and zone
geometry, therefore heating and floor area, therefore **every pooled EUI in `results/RESULTS_EU-11.md`**.
This is the `D-EU-35` desync again, and its rule stands — the pop-up and the simulated IDF must never
describe different geometry. `EU-13B` `T09` is written **blocked**: rebuild the IDFs locally, report the
zone-count deltas and the array-size estimate, **and stop**. No `sbatch` without an explicit instruction.

Prompt: [`prompts/PROMPT_EU-13B_dwelling_layout_scheme_conformance.md`](prompts/PROMPT_EU-13B_dwelling_layout_scheme_conformance.md)
— `T01` conservation · `T02` 8/floor cap · `T03` `ConvexToConcave`/`EdgeTo4` regularization · `T04` the
ruled grid · `T05` morphological branching · `T06` core **(blocked, `D-EU-36`)** · `T07` habitability
correction + the `Unconditioned core: Yes` header that still contradicts its own side-car
(`generate_eu_3d_viewers.py:401`) · `T08` re-emit and report · `T09` resimulation **(blocked)** · `T10` the
`FINDING 203` census **(measure only)**.

🟡 **`EU-14B` — OPENED 2026-08-28: Bologna's layouts, and the emitter that corrupts its manifest.** Bologna
is the only district with **0 side-cars** and no floor-plan pop-up, because
`scripts/emit_eu11_layout_sidecars.py` is incompatible with the ISTAT-imputed provenance path — a test run
wiped `geometry_outcome` to NaN across the whole manifest and was recovered only by a clean re-harvest from
Speed. 🔴 **That script must not be pointed at Bologna until its safety test is green.** The package also
owns the honest census of the **408** buildings that reach no dwelling count even after the four-tier
cascade and the **16** excluded pre-run, and a report — not a correction — on whether the new zoning moves
`FINDING 199`'s INCOMPATIBLE (Too Low) verdict. Runs **after** `EU-13B`, so Bologna arrives already
conforming instead of inheriting the defects.
Prompt: [`prompts/PROMPT_EU-14B_bologna_layout_binding.md`](prompts/PROMPT_EU-14B_bologna_layout_binding.md).

⚪ **Next free identifier `D-EU-38`, next free finding `FINDING 205`.**

⚠ **Three blockers are MEASURED, not assumed, and the executor must resolve them before any run.**
Per-attribute completeness of `02_residential_manifest.gpkg`, counted 2026-08-28:

| District | residential | `year_built` | `levels` | `height_m` |
|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | 1,194 | **0** | 1,028 | 0 |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 522 | 530 | 530 |
| `GB-LDN-STDUNSTANS` | 1,242 | **1** | 1,128 | 0 |
| `IT-BOL-GALVANI2` | 1,220 | **0** | **0** | 0 |

TABULA assignment needs an age band, and geometry needs a storey count; Bologna currently has neither.
The `D-EU-22` probe measured the ceiling of each open source and it has not moved: **ES is solved on disk**
(`es_catastro_attribute_sidecar.csv`, observed year on **1,183 of 1,194**, `D-EU-23` Option G1);
**GB is `CREDENTIAL_BLOCKED`** — `epc.opendatacommunities.org` is retired and the successor requires a
GOV.UK One Login bearer token, with the join surface intact (postcode on 1,176 of 1,242) and
`gb_epc_certificates.csv` holding 8,623 fetched certificates carrying `age_band`; **IT is
`NO_PER_BUILDING_YEAR_IN_ANY_OPEN_SOURCE`** — ISTAT tract epochs are a statistical prior, never an
observed year, while building **height** for Bologna does exist unread in the portal layer
`c_a944ctc_edifici_pl` (`altezza_gr`, `quota_gron`, `quota_pied`, `volume`, 65,744 records).

⚡ **Compute rule.** Speed only, `sbatch --array` fire-and-forget, never the login node; EnergyPlus
**23.1.0 Ubuntu20** under `/speed-scratch/o_iseri/openubem/tools/`, pattern
`scripts/cluster/submit_fleet_t08.sbatch`, waves under the ~20k task cap. 🔴 The Speed engine is a
**different binary and platform** from the Windows 23.1 that produced `s2_campaign_v3`: per `FINDING 187`
and `FINDING 190` a Speed number and the **60.7087 kWh/m²** Lyon figure are **not the same measurement**,
and Lyon must therefore be re-run on Speed inside this campaign rather than carried across.

**Two closing deliverables, both prompt-driven and executed externally:** the results are bound into the
four district viewers (`openubem/outputs/3D/eu_*_viewer.html` + their `eu_*_data/` folders, the model in
`docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §8.5), and the resulting EUIs are validated against
external published sources by deep research (`DeepResearch/DR12_*`). Both are **DONE**, audited PASS in
`validation/VALIDATION_EU-11B_viewer_integration_2026-08-28.md`. Full harvest + DR12–16 write-up is
`results/RESULTS_EU-11.md` (moved from the arc root 2026-08-28 — cite by this path, not the old one).
Prompts: `prompts/PROMPT_EU-11_full_district_campaign_speed.md`,
`prompts/PROMPT_EU-11B_viewer_result_integration.md`,
`DeepResearch/DR12_eui_external_validation_brief.md`. Next free id `D-EU-36` (`D-EU-33` dwelling-layout
coverage, `D-EU-34` Bologna reopening, and `D-EU-35` geometry/simulation desync all ruled 2026-08-28 and
executed the same day — see above), next free finding `FINDING 200` (196 and 197 are spent — a
fabricated-submission finding and a real schedule-shipping bug found during `EU-11`'s Speed submission —
see the director prompt's newest box for both; 198 is the Lyon composition-vs-EUI finding, 199 is Bologna's
DR16 INCOMPATIBLE verdict, both above).

---


🔴 **`G8.0` is RULED and CARRIED, not cured — `D-EU-30` Option A, 2026-08-28.** It stands at **FAIL
99/121 with a stated exclusion of 29**, and **must never be reported as PASS on the strength of that
ruling**: the standard that excludes the 29 is stricter than the gate's own. Of the 121 `f>0` perimeter
cells, **99** have an `f=0` control that merely completed 3/3 — the gate's criterion — but only **92**
have one that is perimeter-grade under `D-EU-28`. The gap is two disjoint groups: **22** cells / 8
archetypes whose control lost a replicate to `ENGINE_FAILED`, and **7** cells / 3 archetypes whose control
completed 3/3 clean and still returned **two distinct `heating_kwh`** — `FINDING 181` inside the
perimeter's own control set. ⚪ No compute was spent and the single agreed re-run stays intact.
`EU-09` and `EU-10` are **Completed with this FAIL carried, not cleared** — acceptance required every
gate *scored*, and a carried FAIL is scored. Record: `debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-30_g8_0_controls_2026-08-28.md`.

🔴 **`FINDING 181` — the diagnostic is AUTHORISED and running at GSSCanada 4J, 2026-08-28.** Scope **90
cells**: the **54** that completed 3/3 with 0 severe, 0 fatal and no marker and still returned different
`heating_kwh` (`it` 47, `uk` 7; 30 archetypes; spread 0.048 / 6.569 / 31.365 % min/median/max), plus the
**8** `D-EU-30` Group I `f=0` controls, plus a **separately labelled arm of the 28** marker-bearing
non-reproducible cells — **28 of 28 are `es`**, so with `FINDING 182` the marker is perfectly confounded
with the fold and that arm can describe the `es` failure mode but can never license an `es` number. Two
arms: 90 × 10 replicates at `--workers 14`, and 90 × 3 at `--workers 1`. ⚪ **It is a diagnostic — no
quotable number, no perimeter, no band, no gate — so it is NOT booked against the spent `D-EU-27` re-run
budget, which stays intact.** ⚠ A clean second-**host** arm is impossible as first specified (the only
other engine is 24.2.0/Linux against a `Version,23.1` IDF); a second Windows box is an **owner ACTION**,
and the arms do not wait on it.

🔴 **`FINDING 185` (4J) — the `.err` kind-set does not point at the model.** Across the certified 149,
the 54 and the 28, the warning-kind set differs across replicates in **0 / 149, 0 / 54 and 1 / 28** cells,
and the 54 draw on exactly the same 8 approved kinds as the 149. The single exception is
`es__ES.ME.MFH.02.Gen.ReEx.001.001__f100`, a sizing artefact downstream of a diverging solution.
**Non-reproducibility is not visible in the error file.**

🔴 **`FINDING 186` (4J) — `fixviewfactors` is associated with divergence but is neither necessary nor
sufficient.** Stratified by fold: `it` 37/47 non-reproducible vs 35/74 certified (OR 4.12, Fisher
p = 6.4e-4); `uk` 0/7 vs 0/75 — the kind **never appears in `uk` at all**, yet 7 `uk` cells still diverge,
and 10 of the 47 `it` ones carry none. **A second, `fixviewfactors`-independent mechanism exists**, so the
equivalent-envelope DESIGN question below cannot be the whole answer.

✅ **`FINDING 187` (4J) — REPAIRED 2026-08-28, suite green at 2,345 / 55.** The manifest now carries
`energyplus_version_declared` (`23.1`, the guard) and `energyplus_version_measured` (parsed from the
binary invoked, `not_run` in dry_run), and `platform` was added to `MANIFEST_FIELDS` with hostname, os,
machine, processor, python_version, energyplus_exe and energyplus_sha256 — `step8_gates`'
`immutable_fields` had demanded `platform` while the writer emitted none, so **G8.14's platform arm could
never have been satisfied by any run**. ⚠ Manifests in `eu_certified_rerun_2026-08-28/` predate this and
carry no `platform`; **they are not retrofitted**. Both defects are registered in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 9. Original statement of the defect:
`eu_cell_runner.py:572` wrote `"energyplus_version": "23.1"` unconditionally, so a 24.2.0 run, a Linux run
and a Windows run all produced manifests reading `23.1`; the measured string existed only in 4J's
`campaign_summary.json`, which our gates never read. Being repaired here alongside `G8.14`'s known
`platform` coverage gap (`MANIFEST_FIELDS` carries no `platform` key while `step8_gates`'
`immutable_fields` requires one) — **a two-host study whose manifests cannot name the host is not
certifiable by our own gate.**

🔴 **`FINDING 181` diagnostic — arms 1, 2 and 3 REPORTED by 4J, 2026-08-28. Contention is
EXCLUDED and the phenomenon reaches INSIDE the certified 149.** Host `tabletop1`, EnergyPlus
`23.1.0-87ed9199d4` Windows, fresh roots; `eu_certified_rerun_2026-08-28/` untouched, nothing under
`openubem/` written, no gate re-scored. **Single-host — these arms predate the `platform` manifest field,
so this is a diagnostic, not a certifiable two-host result.** `FINDING 181` itself stays **OPEN**: the
mechanism is still unidentified.

🔴 **`G8.1`–`G8.4` are recorded NOT SCOREABLE on this engine — `D-EU-31` Option A, 2026-08-28.** They
compare a cell against a re-run of itself (`openubem/validation/step8_gates.py:579-590`), and `FINDINGS 188`–`191`
show that comparison cannot pass reliably on any cell of this engine. They are **carried with that reason,
exactly as `G8.0` is carried as FAIL, and must never be reported as PASS.** `EU-09` therefore reads
**8 PASS / 1 FAIL / 4 VACUOUS / 4 NOT SCOREABLE** (was 12 / 1 / 4). ⚪ No gate code was changed and no gate
was re-run.

🔴 **`FINDING 190` — it is not worker contention.** Power-matched (arm 1's first three replicates vs
arm 2's three): pooled **52/85 (61.2 %)** at `--workers 14` vs **47/83 (56.6 %)** at `--workers 1`;
**`uk` is identical serially, 1/11 vs 1/10** — the residual `uk` mechanism survives unchanged. Set overlap
37 both / 15 parallel-only / **10 serial-only**, so divergence is not even nested. Worker count moves the
rate (71/90 at ten parallel replicates), not the phenomenon.

🔴 **`FINDING 188` — `completed` is a random variable, not a cell attribute.** Same cell, same IDF,
same weather, same binary: completes in some replicates, `ENGINE_FAILED` in others. Arm 1: **64 of 90**
inconsistent. Arm 3: **78 of the 149 certified cells failed to complete in at least one of ten re-runs**,
per-replicate `engine_failed` 8–18 with no trend.

🔴 **`FINDING 189` — not bistability, a continuum.** Distinct `heating_kwh` per cell over ten
replicates reaches **8 states** (arm 1; 52 of 90 show ≥ 3) and 4 (arm 3). Worst:
`es …MFH.06…f015` **79.11 %** over 8 states; `it …MidClim.TH.07…f015` 35.16 % over 4. **A three-replicate
comparison samples this distribution at low resolution and with bias.**

🔴 **`FINDING 191` — the `D-EU-28` certification criterion is luck-driven.** Over ten replicates
**53 of 149 (35.6 %)** of the certified cells produce more than one distinct `heating_kwh` (`it` 30/74,
`uk` 23/75). Per-cell probability that three draws land on one value: **mean 0.859, median 1.000, 13 cells
below 0.5**. Worst inside the perimeter: `uk …AB.04…f050` **79.14 %**, `uk …AB.03…f015` 73.67 %,
`uk …AB.03…f000` 73.64 %. The same statistic on the 90 known-bad cells is mean 0.390 / median 0.173 —
**the certified set is decisively better, it is not clean.** This is `D-EU-31`.

🟢 **`FINDING 192` — the fold aggregate survives.** Basis = cells complete in all ten replicates
(**71 of 149**; `it` 35, `uk` 36), like-for-like sums: **`it` spread 0.157 %** across ten independent
re-runs (per-`f` 0.435 / 0.216 / 0.594 / 0.052 / 0.558 %). Per-cell chaos averages out at fold level.
All ten sums were distinct → the aggregate is **numerically stable, NOT bitwise reproducible**. `uk` moves
**11.498 %** (`uk|f000` alone 58.54 %) — an independent reason not to lift `D-EU-26`'s `uk` bar.
⚠ The tolerance is measured on **35 `it` cells, not the 74** carrying 108.25 kWh/m².

⚠ **`FINDING 186` AMENDED by 4J — the odds ratio 4.12 must no longer be quoted.** It was measured on
3-replicate labels, where a cell is labelled divergent only if divergence is frequent, so part of it was a
detection-power artefact. At ten replicates the stratification largely washes out (`it` fvf True/False:
92.1 % vs 84.6 % in arm 1, 48.6 % vs 33.3 % in arm 3). **The conclusion stands — associated, neither
necessary nor sufficient — the effect size does not.** `uk` still diverges 23/75 with the kind never
appearing, so the equivalent-envelope DESIGN question cannot explain `uk`.

⚪ **`FINDING 181`'s original `es` clause stands.** For `uk` and `it` it is closed by construction under
`D-EU-27`'s three-replicate certification. It is the sole precondition to the single agreed re-run with
GSSCanada 4J, which is otherwise **SPENT** — one re-run, not one per ruling.

⚪ **The equivalent-envelope method is an unruled DESIGN question.** The zone is deliberately unenclosed
(`openubem/idf/european_box.py:46-57`, the `EquivalentEnvelope` contract), which is what produces
`FixViewFactors: View factors not complete` and windows on `OtherSideCoefficients`. Flipping the S0 floor
normals **was tried and reverted** — it cleared the tilt warning and turned a three-of-three identical
cell into one fatal in three. **Do not re-try it without new evidence.**

🔴 **`D-EU-32` — ruled Option A on 2026-08-28 and executed the same day: the `FINDING 181` settling
experiment.** Three arms × three representative cells × ten replicates, **90 runs in 206.8 s**, serial, in
fresh scratch roots under `_tmp_f181/t05/`; **no promoted campaign artefact was read or written and no
`openubem/` source was modified**. Cells: `uk…GB.ENG.AB.04…f100`, `it…IT.MidClim.SFH-TH.07…f100`,
`it…IT.MidClim.SFH.07…f000`.

- **Arm E0 (baseline control, same session, unmutated)** — added to the ruled design (60 → 90 runs) and
  load-bearing, since a null `E1` without a same-session control would be unreadable: `it…SFH-TH.07…f100`
  9/10 completed, **4 states**, 28.56 %; `it…SFH.07…f000` 6/10 completed, **4 states**, 26.80 %;
  `uk…AB.04…f100` 8/10 completed, 1 state, but **2 of 10 runs failed**. The session reproduces the known
  behaviour, so `E1` and `E2` are readable. `E0` is a control and is cited nowhere as a result.
- **Arm E1 (Zone/System/Plant sizing disabled, `SizingPeriod` removed)** — **H8 is REFUTED**: divergence and
  intermittent engine failure persist identically. `uk…AB.04…f100` spread **87.97 %** over 2 states,
  2 fatals; `it…SFH-TH.07…f100` **40.58 %** over 5 states, 2 fatals; `it…SFH.07…f000` **34.30 %** over
  5 states, 1 fatal.
- **Arm E2 (`OMP_NUM_THREADS=1`)** — **OpenMP threading is EXCLUDED** as the channel.
- **The E1 mutation is verified to have taken, not assumed**: the saved E1 IDF carries **0 `SizingPeriod:`
  objects** and all four sizing flags `No`, and **`epluszsz.csv` is absent from every E1 run directory and
  present in every E0 one**. The sizing pass genuinely did not execute, and the divergence survived it.

🔴 **`FINDING 195` — what this licenses, and no more.** The mechanism is **per-process and internal to
the EnergyPlus 23.1 Windows binary**, acting on the ill-conditioned S0 equivalent envelope (unenclosed zone,
massless envelope, openings on synthetic hosts). ⚠ **The specific channel — ASLR, floating-point
contraction, uninitialised state — is NOT measured by this experiment and may not be quoted as
established.** What is established is that it is neither the sizing pass (E1) nor OpenMP threading (E2), and
neither the harness, the inputs nor the environment (`FINDING 193`); `FINDING 194` places the divergence in
the sizing pass itself (117/117 window fatals on the first fenestration surface during
`ANNUALSIZINGPERIOD`), which E1 then shows is not its cause.

⚡ **Speed was offered for this experiment and declined, with a reason**: Speed is Linux and carries a
**different EnergyPlus binary**, so runs there test a different build and cannot address `H3`; and
`FINDING 190` had already excluded worker contention, which makes **serial execution a requirement, not a
convenience**.

🟢 **`FINDING 181` is CLOSED — DECLARED AND BOUNDED, not cured.** It is closed under `D-EU-31` /
`FINDING 192`: cell-level claims stay barred, and the fold aggregate **`it` = 108.25 kWh/m² ± 0.16 %**
(measured on 35 of the 74) is retained. Records:
`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-32_finding181_settling_experiment_2026-08-28.md`,
`implementation/previous/DONE_PLAN_deu32-finding181-settling-2026-08-28.md`,
`outputs/f181_t05_probes.csv`.

**Decisions: all three 2026-08-28 rulings ruled and executed; one work package still live.** `D-EU-33`
(dwelling-layout full coverage) ruled 2026-08-28 was executed the same day and closed, including a
post-delivery audit fix (§3). `D-EU-34` (Bologna reopening) ruled the same day completed as `EU-14` (Speed
job `1295646`, harvested — pooled EUI 55.5346 kWh/m², `FINDING 199`). `D-EU-35` (geometry/simulation desync,
§3) ruled Option 1 and
executed the same day — Madrid/Lyon/London resimulated and harvested, `results/RESULTS_EU-11.md` updated,
`FINDING 198` recorded (Lyon). Before them, `D-EU-32` was ruled **Option A** on 2026-08-28 and executed the
same day. `D-EU-31` before it was documentation-only, zero compute; record
`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-31_reproducibility_perimeter_2026-08-28.md`.
Next free identifier: `D-EU-36`; next free finding `FINDING 200`. **All fourteen `EU-01`–`EU-14` work
packages are Completed.**

---

## 4. Latest ruling — `D-EU-29`, 2026-08-28, Option A, executed the same day

`EU-09` had scored `G8.15` **FAIL 149/149** against an **empty** approval set, because the only ruled
`approved_warning_kinds` list had been ruled for the `S2` bundle, not for the campaign.

All three replicates of all 149 perimeter cells were read on this side
(`openubem/outputs/eu_certified_rerun_2026-08-28/`, 0 files missing): **eight distinct kinds — six
universal 149/149** (`calculated design cooling load for zone`, `processscheduleinput`, `managesizing`,
`getvertices`, `getsurfacedata`, `calculatezonevolume`) **and two `it`-only**, `fixviewfactors` on 35
cells / 9 archetypes and `entered zone volumes differ from calculated zone volume(s).` on 13 cells / 3
archetypes. ⚪ **No cell's warning-kind set differs across its three replicates** (0 of 149).

All eight are approved, with `getvertices`, `calculatezonevolume`, `fixviewfactors` and the
entered-volume mismatch recorded as **stated S0 design assumptions, never as "benign"**. The gate was
**re-scored with `evaluate_warning_gate` itself, not asserted**: `G8.15` **PASS 149/149**, 0 untriaged.

🔴 **`getvertices` is REFUSED on the `S2` perimeter and APPROVED here, deliberately and only here** — on
`S2` it caused `FINDING EU-S2-07` (ventilation loss understated 57.74×) and was repaired, whereas the S0
equivalent envelope emits independently sized, non-overlapping faces by contract. **Every entry in
`openubem/data/campaign/eu_approved_warning_kinds_v1.0.json` therefore now carries a `perimeter` field
(`s2_bundle` / `campaign_149`); a kind approved on one perimeter is not approved on the other — read the
field.** ⚪ The other refused `S2` kind, `indicated zone volume <`, is **absent from all 149**.

⚪ **The ruling moved no number**: perimeter 149, five-`f` set 15 pairs, `FINDING 184` untouched, every
`idf_sha256` standing, no compute. Ruling record:
`debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-29_approved_warning_kinds_2026-08-28.md`.

---

## 5. Where things are

| What | Where |
|---|---|
| Frozen history — every ruling, finding, gate table, caveat and acceptance record | `previous/MVP_european_locations.md`, `previous/WALKTHROUGH_european_locations.md` |
| Append-only progress log (the source of the status table) | `content/walkthrough_progress_log.csv` |
| Open and ruled decision requests | `debugs/docs/` (open), `debugs/docs/DONE-docs/` (ruled) |
| Plan in force | `implementation/` — holds only the plan in force; completed plans go to `implementation/previous/` with an OPEN-33 citation sweep |
| Director prompt for a fresh session | `prompts/DIRECTOR_PROMPT_european_locations.md` |
| 🔴 `EU-13B` acceptance target — the worked example an executor is validated against | `EXAMPLE_dwelling_layout_validation_2026-08-28.md` — the 8 sample buildings with exact expected zone counts, grids, circulation and facade contacts (§6 is the acceptance test), the fleet coverage census against the `D-EU-36` 95 % bar, and `FINDING 204`; drawings at `content/eu13b_sample_plan_*.svg` |
| `EU-13B` sample execution, drawn before dispatch | `https://claude.ai/code/artifact/3fe940e8-231d-459c-b46f-fb9daa1995ce` ("Dwelling Plans Redrawn") — the 8 viewer buildings as-simulated beside as-ruled; prototype only, no repository code changed |
| Executor prompts in force (plan-only, not yet dispatched) | `prompts/PROMPT_EU-13B_dwelling_layout_scheme_conformance.md`, `prompts/PROMPT_EU-14B_bologna_layout_binding.md` |
| Method of record for floor layouts | `MVP` §4.2–§4.4 + `content/figure_4_2_dwelling_layout_schemes.svg`, and `GSSCanada/.../Step8_docs/IMP_step8/outputs/floor_layout_generation_report.md` §3, §5–§9 |
| `EU-11`/`EU-14` result write-ups | `results/RESULTS_EU-11.md`, `openubem/outputs/eu_evidence/EU-14/RESULTS_EU-14.md` |
| Campaign run on disk | `openubem/outputs/eu_certified_rerun_2026-08-28/rep{1,2,3}/` |
| Perimeter source table | `outputs/deu27_rerun_cells.csv` (1,530 rows = 510 cells × 3) |
| Frozen boundary contract | `openubem/data/campaign/eu_campaign_cell_spec_v1.0.json` (`FROZEN_PINNED`, `510 510 22`) |
| Ruled warning kinds | `openubem/data/campaign/eu_approved_warning_kinds_v1.0.json` |

**Suite baseline:** `pytest -q -n 8 tests/` → **2,345 passed / 55 skipped** in ~7 min. Cite the
enumerated 55-skip list, never the bare count.
