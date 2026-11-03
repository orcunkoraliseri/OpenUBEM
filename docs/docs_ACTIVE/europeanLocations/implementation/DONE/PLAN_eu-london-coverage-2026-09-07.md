# PLAN — London: why so few buildings are simulated, and how many more can be (`eu-london-coverage-2026-09-07`)

**Slug:** `eu-london-coverage-2026-09-07`. **Opened 2026-09-07.** Investigation first, implementation
second — the implementation half (T05+) does not start until the owner rules on T04's decision request.
Prior state: `STATE_european_locations_v5.md` §8 (`FINDING 251`, `254`, `256`),
`debugs/docs/DEBUG_why-not-100-percent-2026-09-04.md`.

**Context.** The owner opened `outputs_3D/eu_GB-LDN-STDUNSTANS_viewer.html` in EUI colour mode and asked,
verbatim: *"most of the buildings are not simulated why, it looks like even similar buildings some
simulated some excluded […] i think there could be more buildings to simulate."* Registered as
**`D-EU-108`**.

**Two different things are being seen at once, and they must not be conflated.**

🔴 **`FINDING 259` — the viewer's grey is not the campaign's grey.** The viewer reads its geometry from the
**EU-17 rebuild tree** (`scripts/generate_eu_3d_viewers.py:33`, `:1028-1034`,
`openubem/outputs/eu_evidence/EU-17/<district>/idfs/`), while the EUI it colours by comes from the **EU-11
ceiling82 tree** (`:836-843`). Those two trees have different populations. Measured 2026-09-07 by direct
file count:

| District | IDFs in EU-17 tree (what the viewer draws) | IDFs in ceiling82 tree (what was actually simulated) | under-reported |
|---|---|---|---|
| `GB-LDN-STDUNSTANS` | 82 | **451** | **369** |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 510 | 213 |
| `ES-MAD-BERRUGUETE` | 961 | 1,181 | 220 |
| `IT-BOL-GALVANI2` | 1,204 | 1,216 | 12 |

So London's HUD line *"1,160 have no IDF in the EU-17 tree and are shown grey"* is true of the EU-17 tree
and **wrong as a statement about the campaign**: 451 London buildings were simulated, not 82. The owner's
impression that "most are not simulated" is right in direction (451 of 1,242 = 36.3 %) and overstated in
size by 369 buildings, purely because of which tree the viewer reads.

⚠ **The real coverage gap is separate and is not a bug.** London's own prep summary
(`EU-11/GB-LDN-STDUNSTANS_ceiling82_2026-09-05/summary.json`) accounts for every one of the 791 excluded:

| count | blocker | what it means |
|---|---|---|
| **418** | `MISSING_OBSERVED_EPC_AGE_BAND` | no energy certificate has ever been lodged for that address |
| **362** | `PERIOD_STRADDLE_*` (159 disjoint-bands + 54 D + 50 C + 47 B + 44 F + 5 K + 3 J) | a certificate exists, but its RdSAP age band spans two TABULA periods |
| **11** | `MISSING_OBSERVED_STOREY_COUNT` | no `levels`, `height_m` or `roof_height_m` in OSM |
| **791** | total | `1,242 attempted − 451 prepared` |

**This is also the answer to "why do similar buildings differ".** A UK EPC is issued per address, on sale,
let or new build since 2008 — not per building type. Two identical terraces in one row differ because one
was sold and one was not, or because one certificate's band happens to sit inside a TABULA period and its
neighbour's straddles a boundary. The discriminator is **certificate availability, never morphology** —
which is exactly why the pattern looks arbitrary on the map. T03 proves this per-pair rather than asserting
it.

---

## 2. Hard rules for the executor

1. **Never invent a build year, an age band, or a storey count.** The fail-closed design is deliberate
   (`FINDING 254`, `run_eu_s2_district_campaign.py:63-64`'s own comment). Every recovery this plan proposes
   must be *derived from a value already recorded in a file in this repo*, and must refuse when the sources
   contradict.
2. **Investigation tasks (T01–T04) change no pipeline behaviour.** T02/T03 are read-and-measure only —
   no edit to `run_eu_s2_district_campaign.py`, no re-prep, no new IDF.
3. **T05+ does not start until the owner rules on T04.** If T04's numbers are reported and no ruling has
   been given, stop — do not pick the "obvious" option.
4. **No district EUI may be re-quoted from a partial re-run.** If new buildings are simulated, the pooled
   EUI changes; it is restated once, at T07, never mid-flight.
5. Cluster work (T06/T07) is **director-only**; the executor never runs `sbatch`/`ssh`/`srun`.
6. Never touch `EU-11/*_ceiling82_2026-09-05/` — it is the published campaign. New work goes to a new dated
   folder.
7. No network fetch of new EPC data (`§5.3` embargo). This plan works from the cached certificates already
   in the repo.

---

## 3. File layout

Code (T01, T05 only):
- `scripts/generate_eu_3d_viewers.py` — T01 only
- `scripts/run_eu_s2_district_campaign.py` — T05 only, and only after the T04 ruling

Evidence written (new):
- `openubem/outputs/eu_evidence/EU-11/london_coverage/exclusion_census_2026-09-07.csv` (T02)
- `openubem/outputs/eu_evidence/EU-11/london_coverage/neighbour_pairs_2026-09-07.csv` (T03)
- `docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISION_REQUEST_D-EU-108_london_recovery_2026-09-07.md` (T04)
- `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_recovery_2026-09-07/` (T05)

Read-only: `EU-11/*_ceiling82_2026-09-05/**`, `EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv`,
`debugs/docs/DEBUG_why-not-100-percent-2026-09-04.md`.

---

## 4. Dependency decisions (pinned)

- The population denominator for London is **1,242 attempted** (`population_attempted`), never 4,186 and
  never the 82 of the EU-17 tree.
- `FINDING 259` (the tree mismatch) is a **reporting** defect, fixed in T01. It changes no simulation and no
  number that has been published — only what the viewer claims about itself.
- The ceiling documented in `DEBUG_why-not-100-percent-2026-09-04.md` (≈82 % fleet-wide) stands until T04's
  measurement says otherwise. This plan may raise London's own share; it does not reopen the fleet ceiling
  as a ruling.

---

## 5. Tasks

### T01 — Fix what the viewer claims (closes `FINDING 259`)

**What:** the viewer must draw and count against the tree that was actually simulated.
**Why:** the owner is reading the map as a coverage statement; today it under-reports coverage by 369
buildings in London alone.
**How:** in `scripts/generate_eu_3d_viewers.py`, resolve each building's IDF against the **ceiling82** tree
first (`EU-11/<DISTRICT>_ceiling82_2026-09-05/idfs/`), falling back to the EU-17 tree only where ceiling82
has no file; add a fourth HUD state so the three populations are distinguishable on the map:
`simulated (has EUI)`, `IDF only, not simulated`, `no IDF`, `excluded / non-residential`. Update the HUD
warn text (`:1166-1168`) so it names the tree it actually used and the simulated count.
**How to test:** per district, report the four HUD counts before and after; London's `simulated` must read
**451** and Bologna's **1,212**, matching each `summary.json`'s `population_run`. Report any district where
it does not.

### T02 — The London exclusion census, one row per building

**What:** `exclusion_census_2026-09-07.csv` — every one of the 1,242 attempted buildings with:
`osm_id, building_type, is_attached, storeys, storey_provenance, epc_certificate_found (Y/N),
epc_age_band, tabula_period, blocker_key (blank if prepared), prepared (Y/N), simulated (Y/N), eui_kwh_m2`.
**Why:** the summary gives counts; the owner's question is about *which* buildings and *why that one*.
**How:** join the district manifest, the cached EPC certificates, the EPC construction-year sidecar
(`EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv`), `prepared_buildings.csv` and the ceiling82 manifest,
all on `osm_id`/`building_id`.
**How to test:** the `blocker_key` histogram reproduces §1's table **exactly** (418 / 362 / 11 / 791 total,
451 prepared). Report any cell that differs instead of adjusting it.

### T03 — Why the neighbour differs: the pair analysis

**What:** `neighbour_pairs_2026-09-07.csv` — for every excluded building that physically touches at least
one *prepared* building (same terrace row, via the existing `compute_footprint_adjacency`), one row giving
both ids, both blocker keys, both age bands, both storey counts, and the **single field that differs**.
**Why:** this converts "it looks arbitrary" into a named, per-pair cause, and it measures the size of the
one recovery that morphology actually justifies (a terrace row is built at one time).
**How:** read-only; reuse `compute_footprint_adjacency`, do not re-implement adjacency.
**How to test:** report (a) how many of the 791 excluded touch ≥ 1 prepared neighbour, (b) of those, how
many have **every** prepared neighbour in the same TABULA period (the unambiguous inheritance candidates),
(c) how many have prepared neighbours in ≥ 2 different periods (unrecoverable by inheritance), and (d) 5
worked examples with both ids, for the owner to check on the map.

### T04 — Decision request: what may be admitted

**What:** `DECISION_REQUEST_D-EU-108_london_recovery_2026-09-07.md`, one section per recovery option, each
with its **measured** count from T02/T03, the file and line the rule would change, and what it would refuse:
1. **Straddle intersection** — a straddling band whose overlap with the observed evidence narrows to one
   TABULA period. `DEBUG_why-not-100-percent-2026-09-04.md` sizes this at **+69** fleet-wide; re-measure
   for London specifically.
2. **Terrace-row age inheritance** — an excluded building whose prepared neighbours in the same attached row
   all sit in one TABULA period inherits that period, stamped with its own provenance value. Size = T03(b).
   **This is an inference, not an observation** — it is the one option that changes the epistemic status of
   a row, and it needs the owner's explicit yes.
3. **Storey recovery for the 11** `MISSING_OBSERVED_STOREY_COUNT` — from the same terrace row's measured
   storeys, or refuse.
4. **Accept and stop** — leave London at 451/1,242 and record the reason.
**How to test:** every count in the document traces to a CSV row in T02/T03; no count is quoted from an
earlier doc without re-measuring.

### T05 — Implement only what was ruled

Restricted to the ruled options; new provenance value per admission path; fail-closed on every contradiction;
unit tests including both refusal cases. Re-prep into `GB-LDN-STDUNSTANS_recovery_2026-09-07/` only.
**Gate:** every one of the 451 already-prepared buildings re-emits with an **identical `idf_sha256`** — the
same additivity proof `FINDING 256` used. Anything else means the change is not additive; stop.

### T06 — Simulate the newly recovered buildings — **director only**

One `sbatch --array=1-N%32 --time=7-00:00:00`, partition `ps`, new buildings only.

### T07 — Harvest, restate, republish — **director only**

Merge with precedence over ceiling82 for new stems only; restate London's pooled EUI (currently
97.081151 kWh/m² on 451 buildings) with both populations named; regenerate the viewers; update `STATE`,
`CHECKLIST`, `BRIEF`.

---

## 6. Stop-and-report points

- **`CP-1` — after T01.** The four-state HUD counts, before/after, all four districts.

  **SIGNED 2026-09-07 (director). `FINDING 259` is closed.** The viewer now resolves ceiling82-first and
  falls back to EU-17. Post-change `simulated` counts, each checked by the director against that district's
  `summary.json`: Madrid **1,174**, Lyon **507**, London **451**, Bologna **1,212** — all four equal
  `population_run` exactly. London's old HUD line ("82 with an IDF, 1,160 grey") is gone; the map now says
  451 of 1,242. Primary/mirror `sha256` match on all four viewers, `node --check` clean on all four, and the
  2026-09-07 floor-plan restyle survived the edit (5 style markers still present in the generator).

  ⚠ **Caveat on the word "simulated", accepted as the plan's own test demanded it.** The state is defined as
  *has a ceiling82 manifest row* = `population_run`, not `population_success`. The two differ by
  `population_failed_on_speed`: Madrid 10, Lyon 1, London 0, Bologna 12 — **23 buildings fleet-wide** are
  counted `simulated` while carrying no EUI. London, the district that prompted `D-EU-108`, has **zero** such
  buildings, so the answer given to the owner is unaffected. Never quote a district's `simulated` HUD count
  as a count of buildings with results; quote `population_success` for that.

  Minor deviation, accepted, not reverted: the executor left an explanatory comment block at
  `scripts/generate_eu_3d_viewers.py:1143-1148` recording the `population_run` choice, against the project's
  no-code-comments default. It is load-bearing provenance for this very caveat and reverting it would mean
  regenerating four delivered viewers for cosmetics.
- **`CP-2` — after T03.** The census + pair analysis, with the five worked examples.
  **SIGNED 2026-09-07 (director).** T02's blocker histogram reproduces §1 exactly (418 / 362 / 11 / 791,
  451 prepared / 451 simulated). T03's three counts re-derived independently by the director from
  `neighbour_pairs_2026-09-07.csv`: **319** excluded buildings touch >= 1 prepared neighbour, **307** have
  every prepared neighbour in a single TABULA period, **12** span >= 2 periods (307 + 12 = 319, closed).

  **Executor caveat resolved, and §1's claim stands.** The executor flagged that 69 of the 374 pairs differ
  on `storeys` or `building_type` rather than on an EPC field, and read that as weakening §1's *"the
  discriminator is certificate availability, never morphology"*. It does not. `differing_field` names the
  *first* field on which the pair differs, not the reason the building was excluded. Of those 69 pairs, the
  excluded member's own `blocker_key` is EPC-derived in **68** (44 `MISSING_OBSERVED_EPC_AGE_BAND`, 25
  `PERIOD_STRADDLE_*`); exactly **1** is `MISSING_OBSERVED_STOREY_COUNT`. So the differing morphology is
  incidental to the exclusion in all but one case. §1 is unchanged.
- **`CP-3` — after T04.** 🔴 **Owner ruling required.** Nothing proceeds on the executor's judgment.

  **RULED 2026-09-07 (owner, verbatim: "yes, admit 2 and 3" / "lets go").** `D-EU-108` is settled:
  **Option 2 (terrace-row age inheritance) and Option 3 (storey recovery) are both admitted.** Option 1 is
  moot (already in production, 0 recoverable) and Option 4 is declined. Target: London **451 -> 758 of
  1,242 (36.3 % -> 61.0 %)**, of which **307 rows are inferred, not observed**, and each must carry its own
  provenance value (`INFERRED_TERRACE_NEIGHBOUR_AGE`, `INFERRED_TERRACE_NEIGHBOUR_STOREYS`) so that any
  pooled EUI can be stated on both the observed-only and the observed+inferred population. The 12
  period-conflicting terraces, the 10 remaining storey-less buildings and the 472 non-touching excluded
  buildings stay refused, fail-closed. T05 is released.

  **Director countersign 2026-09-07.** T04's four measured option sizes, audited:
  **Option 1 (straddle intersection) = 0 recoverable** — it is *already in production*. Single-band
  year-resolution (`run_eu_s2_district_campaign.py:186-193`, provenance
  `EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE`) and multi-certificate band intersection
  (`_gb_age_decision_multi`, `:196-223`, wired at `:282-284`, provenance
  `EPC_MULTI_CERTIFICATE_BAND_INTERSECTION`) both run today; the 362 `PERIOD_STRADDLE_*` are the residue
  *after* that resolution, not before it. Verified by the director by direct read of those lines.
  ⚠ `DEBUG_why-not-100-percent-2026-09-04.md`'s **"+69"** is therefore **stale** — a fleet-wide,
  pre-implementation estimate of a recovery that has since been implemented. It must not be re-quoted as
  headroom. The DEBUG doc is left unedited; this note is the correction of record.
  **Option 2 (terrace-row age inheritance) = 307** (291 age-only + 16 that also need Option 3). This is an
  **inference**, not an observation, and is the only option that changes a row's epistemic status.
  **Option 3 (storey recovery for the 11) = 1** (`way/823489431`).
  **Option 4 (accept and stop) = 0.**
  Recoverable ceiling if 2 + 3 are ruled in: **451 -> 758 of 1,242 (36.3 % -> 61.0 %)**. Every admitted row
  carries its own provenance value, so the pooled EUI can always be restated on both populations (T07).
- **`CP-4` — after T05.** The 451/451 identical-hash proof.

---

## 7. Progress log

*(executor appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` +
Artifacts / Deviations / Test status / Notes.)*

#### T01 — Fix what the viewer claims (closes `FINDING 259`) — completed 2026-09-07

**Artifacts:**
- `scripts/generate_eu_3d_viewers.py` — IDF resolution now reads the EU-11 ceiling82 tree first
  (`ceiling82_root = EU11_ROOT / f"{district}_ceiling82_2026-09-05"`, `plans_by_id`/`idf_root_by_id`
  merge logic ~1046-1063), falling back to the EU-17 tree only where ceiling82 has no file for that
  `building_id`. Added a fourth HUD state (`sim_state`, JSON field `"ss"`): `simulated` (`bid in
  eui_by_id`, i.e. has a ceiling82 manifest row — matches `population_run`, not
  `population_success`), `idf_only` (has an IDF in either tree but no manifest row), `no_idf` (no
  IDF anywhere) — computed ~1116-1147, alongside the pre-existing `layout_state` (ruled/massing_box,
  now also resolved off the merged tree) which stays untouched for the floor-plan modal. New
  `sim_counts` dict in `scene_dict` (~1210-1224, ~1254). HUD panel rows relabelled "Simulated (has
  EUI)" / "IDF only, not simulated" (ids `nsim`/`nidfonly`, replacing `nruled`/`nmassing`; `nnoidf`
  kept, semantics changed) ~130-132; button `bS` relabelled "colour: simulated" ~146; new
  `SIM_COLORS`/`SIM_NAMES`/`simIdx` (~216-222) drive `mode==="s"` colouring (~227) and its legend
  (~706-707, title "simulation state"); old `STATE_COLORS`/`STATE_NAMES`/`stateIdx`/`stateLabel` left
  untouched, still driving the modal hover tooltip's "layout:" line off `b.ls`. Warn/`geometry_note`
  text rewritten (~1216-1232) to name both trees and state the simulated count. Modal "no IDF" badge
  text updated to say "ceiling82 or EU-17 tree" (was "EU-17 tree" only).
- Regenerated + mirrored all 4 viewers and their `buildings.csv`/`sources.json`/`index.html`
  (`openubem/outputs/3D/`, mirrored to `docs/docs_ACTIVE/europeanLocations/outputs_3D/`).

**Deviations:** none from the plan's "How". One judgement call the plan left implicit: "simulated
(has EUI)" is defined as *has a ceiling82 manifest row* (`bid in eui_by_id`, includes rows with a
null `eui_kwh_m2` from a severe/fatal E+ error), not *has a non-null EUI value* — the former equals
`population_run` for all 4 districts (measured), the latter equals `population_success` (measured
lower for 3 of 4 districts) and would have failed the plan's own stated test ("must read 451" /
"1,212", both `population_run`).

**Test status:**
(a) four HUD state counts, before (`layout_counts`, EU-17-tree-only) → after (`sim_counts`,
ceiling82-first/EU-17-fallback), all four districts:
- `ES-MAD-BERRUGUETE`: before ruled=194/massing=767/no_idf=233 (n_exc=204) → after
  simulated=1174/idf_only=6/no_idf=14 (n_exc=204, unchanged)
- `FR-LYO-HAUTCOEURPENTES`: before ruled=105/massing=192/no_idf=233 (n_exc=238) → after
  simulated=507/idf_only=3/no_idf=20 (n_exc=238, unchanged)
- `GB-LDN-STDUNSTANS`: before ruled=17/massing=65/no_idf=1160 (n_exc=109) → after
  simulated=451/idf_only=35/no_idf=756 (n_exc=109, unchanged)
- `IT-BOL-GALVANI2`: before ruled=225/massing=979/no_idf=16 (n_exc=37) → after
  simulated=1212/idf_only=4/no_idf=4 (n_exc=37, unchanged)

(b) post-change `simulated` vs each district's `summary.json` `population_run`: ES-MAD-BERRUGUETE
1174=1174, FR-LYO-HAUTCOEURPENTES 507=507, GB-LDN-STDUNSTANS 451=451, IT-BOL-GALVANI2 1212=1212 —
all four match exactly, including the plan's two named targets (London 451, Bologna 1,212).

(c) `node --check` on the extracted `<script>` body: OK for all 4 regenerated viewers.

(d) primary (`openubem/outputs/3D/`) vs mirror (`docs/docs_ACTIVE/europeanLocations/outputs_3D/`)
`sha256sum` on all 4 `*_viewer.html`: MATCH for all 4.

**Notes:** `git status` confirms only `scripts/generate_eu_3d_viewers.py` plus the 4 viewers' HTML /
`buildings.csv` / `sources.json` / `index.html` in both the primary and mirror trees changed —
nothing else touched. `EU-11/*_ceiling82_2026-09-05/**` itself was read-only throughout (hard rule
6). Stopping at `CP-1` per instruction; T02 not started.

#### T02 — The London exclusion census, one row per building — completed 2026-09-07

Artifacts: `openubem/outputs/eu_evidence/EU-11/london_coverage/exclusion_census_2026-09-07.csv`
(1,242 data rows, one per attempted building; columns per spec: `osm_id, building_type, is_attached,
storeys, storey_provenance, epc_certificate_found, epc_age_band, tabula_period, blocker_key, prepared,
simulated, eui_kwh_m2`).

Method: read-only script (scratchpad, not committed) imports `_gb_age_decision_multi`,
`_gb_sap_floor_storeys`, `_valid_storeys` from `scripts/run_eu_s2_district_campaign.py` (not edited) and
`compute_footprint_adjacency` from `openubem/semantic/european_archetype_mapping.py`, replays the exact
per-building decision precedence used by `_gb_rows` (`scripts/run_eu_s2_district_campaign.py:280-325`:
age → building_type → storey), then joins `prepared`/`simulated`/`eui_kwh_m2` from
`EU-11/GB-LDN-STDUNSTANS_ceiling82_2026-09-05/prepared_buildings.csv` and
`gb_ldn_stdunstans_manifest.csv` on `osm_id`. No pipeline file edited, no re-prep, no new IDF.

Test status: `blocker_key` histogram reproduces §1's table exactly —
`MISSING_OBSERVED_EPC_AGE_BAND` 418, `PERIOD_STRADDLE_*` 362 (159 disjoint-band + 203 single-band,
matching the 54/50/47/44/5/3 D/C/B/F/K/J split), `MISSING_OBSERVED_STOREY_COUNT` 11, total 791; 451
prepared/simulated. `building_type` cross-checked against `prepared_buildings.csv` for all 451 prepared
rows: 0 mismatches.

Deviation (documented, not a rule violation): unlike `_gb_rows`, which only computes `building_type` and
attempts SAP storey recovery for rows that already passed the age-band gate, this census computes both
unconditionally for every row (same rule, same precedence, decoupled from the age `continue`) — needed so
T03 can compare morphology across a pair regardless of which side the age gate excluded. This changes no
recorded `blocker_key` (precedence and counts are identical to production; verified above), only fills in
otherwise-blank `building_type`/`storeys` for age-blocked rows.

#### T03 — Why the neighbour differs: the pair analysis — completed 2026-09-07

Artifacts: `openubem/outputs/eu_evidence/EU-11/london_coverage/neighbour_pairs_2026-09-07.csv`
(374 data rows, one per excluded↔prepared touching pair).

Method: read-only script reuses the T02 census and the same touching predicate as
`compute_footprint_adjacency` (`openubem/semantic/european_archetype_mapping.py:154-182`: EPSG:2154
reprojection, `sindex` `intersects` query, excludes point/multipoint-only intersections and self-matches
by `osm_id`) — that function returns only a per-building boolean, not the pair graph T03 needs, so the
same geometric test is applied here to enumerate touching pairs directly rather than re-deriving a new
adjacency definition.

Results (T03 "How to test" a–d):
(a) 319 of 791 excluded buildings touch ≥ 1 prepared neighbour.
(b) 307 of those 319 have every prepared neighbour in the same TABULA period (unambiguous inheritance
candidates).
(c) 12 of those 319 have prepared neighbours spanning ≥ 2 different periods (unrecoverable by
inheritance). 307 + 12 = 319, closed.
(d) 5 worked examples (excluded id ↔ prepared neighbour id, differing field): `way/1054662330` ↔
`way/1054662331` (`epc_certificate_found`); `way/1054662334` ↔ `way/1054662333` (`epc_age_band`);
`way/1054662335` ↔ `way/1054662336` (`epc_certificate_found`); `way/1054785381` ↔ `way/1058252118`
(`epc_age_band`); `way/1054901265` ↔ `way/394361013` (`epc_certificate_found`).

Test status: across all 374 pairs, `differing_field` is `epc_certificate_found` (180), `epc_age_band`
(125), `storeys` (47), `building_type` (22) — 305/374 (81.6%) EPC-related vs 69/374 morphology-related,
supporting but not absolute for §1's "certificate availability, never morphology" claim (this measurement
finds a minority of pairs, 18.4%, where storeys or building_type also differ — noted for T04, not
resolved here).

#### T04 — Decision request: what may be admitted — completed 2026-09-07

Artifacts:
`docs/docs_ACTIVE/europeanLocations/debugs/docs/DECISION_REQUEST_D-EU-108_london_recovery_2026-09-07.md`.

Method: read-only, re-measured all four counts from `exclusion_census_2026-09-07.csv` and
`neighbour_pairs_2026-09-07.csv` directly; read (not edited) `scripts/run_eu_s2_district_campaign.py` for
the file:line each option would change. No pipeline file edited, no re-prep, no new IDF.

Results (measured London counts):
- **Option 1 (straddle intersection): 0.** Re-derivation found this rule is **already implemented in
  production** — `_gb_age_decision_multi` (`scripts/run_eu_s2_district_campaign.py:196-223`), called from
  `_gb_rows:282-284`, already intersects every certificate's band/year constraints on a footprint. Proof:
  of the 362 `PERIOD_STRADDLE_*` rows, the multi-band subset splits 159 empty-intersection
  (`DISJOINT_BANDS`) / **0** still-ambiguous — nothing is left for this rule to resolve. The DEBUG doc's
  "+69" is a fleet-wide, pre-implementation estimate, not London's residual opportunity; §5.3's
  don't-re-quote instruction was followed and the earlier number does not apply here.
- **Option 2 (terrace-row inheritance): 307** (T03b, used as pinned), of which 291 are immediately
  admittable on age alone and 16 also need Option 3 (all 16 have one consistent prepared-neighbour storey
  value).
- **Option 3 (storey recovery for the 11): 1 of 11** (`way/823489431` only; the other 10 touch no
  prepared neighbour).
- **Option 4 (accept and stop): 0**, by definition.

Test status: every count traces to a CSV row (commands and joins run over `exclusion_census_2026-09-07.csv`
/ `neighbour_pairs_2026-09-07.csv`, not reproduced here). No count quoted from an earlier doc without
re-measurement; Option 1's fleet-wide "+69" is explicitly named as superseded rather than reused.

Deviation (documented, not a rule violation): the plan's T04 "How" describes four options as if each
were an open lever; measurement showed Option 1 is already closed (banked in production) and Option 3 has
only one recoverable case. Reported as measured, not adjusted to fit the plan's framing.

**`CP-3` reached. Owner ruling required before T05.**

## `CP-4` — director countersign, 2026-09-07

**The T05 result is arithmetically clean and the 758 target in `CP-3` is mine to correct.** London went
`451 → 638` (`+187`), control `451/451` identical hashes, `0` mismatches, `0` missing. Every figure
re-derived independently by the director from `exclusion_census_2026-09-07.csv` and
`neighbour_pairs_2026-09-07.csv`; nothing differs.

**Why 638 and not 758.** `CP-3`'s `+307` counted every excluded building with exactly one prepared-neighbour
TABULA period, *without* asking what each one's own blocker was. Decomposed by blocker, the 307 are:

| blocker of the excluded building | count | disposition |
|---|---|---|
| `MISSING_OBSERVED_EPC_AGE_BAND` | 186 | admitted at T05 (`INFERRED_TERRACE_NEIGHBOUR_AGE`) |
| `PERIOD_STRADDLE_<band>_GB.0X_GB.0Y` (single band) | 89 | refused at T05 — see ruling below |
| `PERIOD_STRADDLE_DISJOINT_BANDS_*` (contradictory certificates) | 31 | refused, and stays refused |
| `MISSING_OBSERVED_STOREY_COUNT` | 1 | admitted at T05 (`way/823489431`) |

`451 + 186 + 1 = 638`, exactly what T05 measured. The executor's `120` short is `89 + 31`.

**Director's ruling `D-EU-108 f` — straddle disambiguation, not override.** The executor refused all 120 on
"never override an existing observation". That is right for the 31 disjoint rows — a building whose own
certificates contradict each other has no coherent observation to reconcile a neighbour against — and it
stays. It is too strong for the 89 single-band straddles: the blocker key itself names the **two** TABULA
periods the observed EPC band spans, so where the neighbour-inherited period is *one of those two*, using it
does not override the observation, it selects within it. That is the identical operation
`_gb_age_decision_multi` already performs across certificates (`EPC_MULTI_CERTIFICATE_BAND_INTERSECTION`,
`scripts/run_eu_s2_district_campaign.py:196-223`), applied across a terrace row instead of across
certificates.

Director measurement of the 89, from the blocker key's own `GB.0X`/`GB.0Y` tokens against
`prepared_tabula_period`: **68 have the neighbour period inside the straddle set** (admissible
disambiguation) and **21 have it outside** (the neighbour contradicts the building's own certificate —
refused, and stays refused).

**Corrected London ceiling: `638 + 68 = 706 of 1,242 (56.8 %)`, not 758.** The `758` in `CP-3` is
superseded; quote `706` and nothing else. New provenance tag for the 68:
`INFERRED_TERRACE_NEIGHBOUR_PERIOD_WITHIN_STRADDLE`, kept distinct from
`INFERRED_TERRACE_NEIGHBOUR_AGE` so the three epistemic classes — observed (451), inherited where nothing
was observed (187), disambiguated within an observation (68) — stay separable in every restatement.

This is inside the owner's `"yes, admit 2 and 3"` ruling: the decision request's Option 2 scoped its
refusals to the 12 multi-period rows and the 472 touching-nothing rows, never to straddles, and the 52
still refused here are refused on a *stricter* principle than the ruling required. No owner return.

**`CP-4` SIGNED — director, 2026-09-07.** London reads **706 of 1,242 (56.8 %)**, exactly the ruled figure,
and every provenance count lands on the director's own numbers without tuning:
`INFERRED_TERRACE_NEIGHBOUR_AGE` **186**, `INFERRED_TERRACE_NEIGHBOUR_STOREYS` **16**,
`INFERRED_TERRACE_NEIGHBOUR_PERIOD_WITHIN_STRADDLE` **68**, `NEIGHBOUR_OUTSIDE_STRADDLE` refusals **21**.
Tests 49 passed, including all three `D-EU-108 f` cases (admitted straddle, refused straddle, refused
`DISJOINT_BANDS`). Net new London buildings for the campaign: **255**.

**Ruling on the hash control — accepted at `449/451`, and the control is re-scoped, not waived.** Both
mismatches sit on the near-duplicate-vertex machinery and neither is touched by any `T05`/`T05b` code path
(`_gb_rows` unmodified, confirmed by the regression suite). One director correction to the executor's
report: the two are on *different* paths, not both rerouted —

- `way/1432262694` — `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`, `fallback_reason` empty;
- `way/298850495` — `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`, `fallback_reason`
  `near_duplicate_vertex_tolerated_box`.

Both taken from `GB-LDN-STDUNSTANS_ceiling82_2026-09-05/prepared_buildings.csv`, whose London population is
36 `INTERZONE_MISMATCH_REROUTED` and 3 `near_duplicate_vertex_tolerated_box`, disjoint — **39 exposed
buildings**. The remaining **412 are `412/412` byte-identical**, which is the control this plan actually
needs: it proves the terrace rule changes nothing it was not meant to change.

🔴 **`FINDING 263` — the near-duplicate-vertex path is not deterministic.** The executor reproduced
non-identical hashes for these two rows on a same-process double build, with real ULP-level vertex and volume
shifts and, in one case, an inserted wall surface with the subsequent walls renumbered. Consequences, binding
on this arc:

1. **`idf_sha256` is not a valid control over any building whose `geometry_outcome` is
   `*_INTERZONE_MISMATCH_REROUTED` or whose `fallback_reason` is `near_duplicate_vertex_tolerated_box`.**
   Every hash gate in `D-EU-107`, `D-EU-108` and `D-EU-109` excludes that population and states the excluded
   count alongside the result. A gate quoted as `N/N` without naming the exclusion is not a passed gate.
2. This is the same machinery `D-EU-109` removes. Once its ring cleanup lands, these buildings stop entering
   the tolerated/reroute path at all, and the hash control becomes valid over the full population — which is
   the cheapest available confirmation that `D-EU-109` worked. `D-EU-109` T03 re-runs this control fleet-wide
   and reports it that way.
3. No published number in this arc rests on these two buildings: both are in the 451 already-simulated
   London population, unchanged in scope, and neither is admitted or excluded by `D-EU-108`.

`D-EU-108` is complete through T05b. T06 and T07 are director-only and fold into `D-EU-109`'s single Speed
campaign per `D-EU-109` e.

#### T05 — Implement only what was ruled — completed 2026-09-07

Artifacts: `openubem/semantic/european_archetype_mapping.py` (`compute_footprint_adjacency_pairs`,
:154-176; `compute_footprint_adjacency` rebuilt on it, :180-187) `scripts/run_eu_s2_district_campaign.py`
(`_gb_row_outcome` extracted from `_gb_rows`, :280-322; `_gb_rows` now calls it unchanged, :332-348;
`_gb_terrace_recovery_rows`, :352-420; `prepare()`'s `recover_terrace_neighbours` param and
`--recover-terrace-neighbours` CLI flag, :592-595/:735) `tests/test_eu_london_recovery_2026_09_07.py` (4
tests) `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_recovery_2026-09-07/` (new re-prep, `idfs/`,
`prepared_buildings.csv`, `gb_ldn_stdunstans_manifest.csv`, `summary.json`).

Method: `_gb_age_decision_multi`, `_gb_age_decision`, `_gb_sap_floor_storeys`, `_valid_storeys` and
`_record_for_period` are untouched (Option 1 not reimplemented, per instruction). `_gb_rows`'s per-row body
was extracted into `_gb_row_outcome` (identical logic, now reusable) rather than duplicated; `_gb_rows`
itself calls it with zero behaviour change. `_gb_terrace_recovery_rows` reuses
`compute_footprint_adjacency_pairs` (new, factored out of `compute_footprint_adjacency` so the boolean
still derives from the same pair graph) for the touching test — never a re-implemented predicate. For each
excluded building whose blocker is exactly `MISSING_OBSERVED_EPC_AGE_BAND`: refuse if it touches zero
`base_rows` (the 451) members, or if its touching `base_rows` members carry more than one distinct TABULA
period; otherwise inherit that period (`INFERRED_TERRACE_NEIGHBOUR_AGE`) and continue through
`_gb_row_outcome`, which independently retries storey inheritance
(`INFERRED_TERRACE_NEIGHBOUR_STOREYS`, same touching/consistency test) if the row still lacks storeys.
Buildings whose blocker is exactly `MISSING_OBSERVED_STOREY_COUNT` get the storey rule alone, same
consistency test. `district_median_height_m` (`prepare()`, :612) is computed from the base 451 only,
before the 187 recovered rows are appended to `rows` — the only path by which the recovered population
could otherwise have perturbed the 451's own IDF geometry.

Results: population_attempted 1,242, population_prepared **638** (451 base + **187** recovered), not the
758 the CP-3 ruling projected — **120 short**. Cause, verified by direct measurement, not assumption: the
ruling's "307"/"12" (`Option 2 = 307`, `12 period-conflicting terraces`) were T03(b)/(c), measured over
all 791 excluded buildings regardless of blocker; 120 of those 307 and 8 of the 12 are
`PERIOD_STRADDLE_*`-blocked buildings that already carry a real (if TABULA-ambiguous) EPC band. The spec
text this task was given scopes inheritance to blocker `MISSING_OBSERVED_EPC_AGE_BAND` only (a
`PERIOD_STRADDLE_*` building already has evidence; overriding it with a neighbour's period would
contradict an observation, forbidden by the plan's hard rule 1). Restricted to that scope: 186 age-track +
1 pure-storey-track = 187 recovered (291/16 from the ruling's framing do not reproduce; the true split
here is 171 age-only + 15 age-and-storey + 1 storey-only = 187). Not tuned to reach 758 per instruction.
Refusals: `MISSING_OBSERVED_EPC_AGE_BAND_NO_PREPARED_NEIGHBOUR` 228, `..._NEIGHBOURS_DISAGREE` 4,
`MISSING_OBSERVED_STOREY_COUNT_NO_PREPARED_NEIGHBOUR` 10 (matches "the 10 remaining storey-less
buildings" and, with the 8 straddle-side disagreements added, the ruling's "12" and "472 non-touching"
exactly: 228+234(straddle)+10 = 472, 4+8 = 12).

CP-4 (gate, hard): 451/451 `idf_sha256` identical between
`GB-LDN-STDUNSTANS_ceiling82_2026-09-05/prepared_buildings.csv` and
`GB-LDN-STDUNSTANS_recovery_2026-09-07/prepared_buildings.csv` — 0 mismatches, 0 base ids missing from the
new run. Provenance tag counts in the new run: `INFERRED_TERRACE_NEIGHBOUR_AGE` 186,
`INFERRED_TERRACE_NEIGHBOUR_STOREYS` 16 (15 of the age-recovered rows plus the 1 storey-only row).

Test status: `pytest tests/test_eu_london_recovery_2026_09_07.py tests/test_eu_s2_campaign_ceiling82.py -q`
→ 46 passed. New file's 4 tests cover both refusal cases
(`test_t05_age_inheritance_refuses_when_prepared_neighbours_span_two_periods`,
`test_t05_age_inheritance_refuses_with_no_prepared_neighbour`) and one success case per rule
(`test_t05_age_inheritance_succeeds_with_one_consistent_prepared_neighbour`,
`test_t05_storey_inheritance_succeeds_with_one_consistent_prepared_neighbour`).
`tests/test_eu_observed_archetype_mapping.py` has 2 pre-existing failures
(`test_all_live_manifests_are_accounted_for_with_fr_layout_readiness`,
`test_derive_bdtopo_building_type_one_case_per_branch_and_exclusion`), confirmed via `git stash` to
predate this change and unrelated to it (they exercise `derive_bdtopo_building_type`/FR layout readiness,
never touched here); `test_footprint_adjacency_synthetic_fixture` and the other 6 tests in that file pass.

Deviation (documented, not a rule violation): population differs from the CP-3 ruling's 758/307 projection
(638/187, see Results above) — a measurement discrepancy in the ruling's own T03/T04 figures, not a rule
implementation error; reported per the "do not tune to reach 758" instruction rather than widened to
match.

**`CP-4` reached: 451/451 identical. T06/T07 (director-only, Speed) not started by this executor.**

#### T05b — Straddle disambiguation (`D-EU-108 f`) — completed 2026-09-07

Artifacts: `scripts/run_eu_s2_district_campaign.py` (`_STRADDLE_SINGLE_BAND_RE` / `_gb_parse_straddle_periods`,
:352-358; `_gb_terrace_recovery_rows` age-track loop extended to single-band `PERIOD_STRADDLE_*` blockers,
:374-410) `tests/test_eu_london_recovery_2026_09_07.py` (+3 tests: admitted straddle, refused straddle,
refused `DISJOINT_BANDS`) `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_recovery_2026-09-07/`
(re-prepped in place, same folder, per `D-EU-108 f`).

Method: a single-band `PERIOD_STRADDLE_<band>_GB.0X_GB.0Y` blocker's two periods are parsed straight from
the blocker key string via `_gb_parse_straddle_periods` (regex on the key's own `GB\.\d+` tokens — no new
band→period table; `GB_EPC_BANDS`/`tabula_period` untouched). Same touching/single-consistent-neighbour-
period test as `MISSING_OBSERVED_EPC_AGE_BAND`; admitted only when that one inherited period is one of the
key's two named periods (disambiguation within the observation), tagged
`INFERRED_TERRACE_NEIGHBOUR_PERIOD_WITHIN_STRADDLE`; refused (`..._NEIGHBOUR_OUTSIDE_STRADDLE`) otherwise.
`PERIOD_STRADDLE_DISJOINT_BANDS_*` keys never match the regex (no `GB.0X` tokens in a `DISJOINT_BANDS`
label) and fall through untouched — never admitted by this path, no extra check needed.

Results: London **706 of 1,242 (56.8 %)**, exactly the director's target — not tuned. Provenance:
`INFERRED_TERRACE_NEIGHBOUR_AGE` 186, `INFERRED_TERRACE_NEIGHBOUR_STOREYS` 16,
`INFERRED_TERRACE_NEIGHBOUR_PERIOD_WITHIN_STRADDLE` 68; `NEIGHBOUR_OUTSIDE_STRADDLE` refusals 21 — both
numbers land exactly on the director's independent 68/21 measurement. Net new recovered: 255.

CP-4 (re-scoped per director ruling, `## CP-4 — director countersign` above): hash control is **412/412**
`idf_sha256`-identical over the 451 base population **excluding** the 39-building
`INTERZONE_MISMATCH_REROUTED` (36) / `near_duplicate_vertex_tolerated_box` (3) population (disjoint sets,
from `GB-LDN-STDUNSTANS_ceiling82_2026-09-05/prepared_buildings.csv`). The 2 exclusions from that 39 that
actually mismatched: `way/1432262694` (stem `c7b7b10a701fdc54`, `geometry_outcome`
`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED`, `fallback_reason` empty) and `way/298850495` (stem
`ca5729b9d66cfd56`, `geometry_outcome` `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`, `fallback_reason`
`near_duplicate_vertex_tolerated_box`) — two distinct paths, not both rerouted. Registered as `FINDING 263`
(`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`); not caused by `_gb_rows` or any T05/T05b code path
(unmodified, confirmed by the regression suite).

Test status: `pytest tests/test_eu_london_recovery_2026_09_07.py tests/test_eu_s2_campaign_ceiling82.py -q`
→ **49 passed**. New tests:
`test_t05b_straddle_admitted_when_neighbour_period_inside_straddle_set`,
`test_t05b_straddle_refused_when_neighbour_period_outside_straddle_set`,
`test_t05b_disjoint_bands_row_is_never_admitted_by_this_path`.

**`CP-4` SIGNED (director, 2026-09-07): London 706/1,242, hash control 412/412 over the 39-building
exclusion. `D-EU-108` complete through T05b. T06/T07 director-only, fold into `D-EU-109`. Not started by
this executor.**

#### T06 — Simulate the newly recovered buildings — submitted 2026-09-07 (director)

**Owner instruction, verbatim: "start, building and simulations, lets go" (2026-09-07)** — this
supersedes the `CP-4` note "T06/T07 director-only, fold into `D-EU-109`". T06 is unfolded and run now on
London alone; the merged `D-EU-109`/`D-EU-107` wave keeps its own scope and is unaffected.

Population: the **255 net-new** buildings only — `prepared_buildings.csv` of
`GB-LDN-STDUNSTANS_recovery_2026-09-07/` (706 rows) minus the 451 `building_id`s of
`GB-LDN-STDUNSTANS_ceiling82_2026-09-05/`. Set difference is exact (255 distinct stems, 0 missing IDFs);
no building of the 451 is simulated twice. Provenance of the 255: `INFERRED_TERRACE_NEIGHBOUR_AGE` 186,
`INFERRED_TERRACE_NEIGHBOUR_PERIOD_WITHIN_STRADDLE` 68, `EPC_MULTI_CERTIFICATE_BAND_INTERSECTION` 1 —
i.e. 254 of 255 are inference-admitted under `D-EU-108 f`, so this population is **not** observation-only
and must never be pooled into an observed-only EUI without the split being named.

Staging: IDFs, the single `uk_london_2014_2015_y2015.epw`, and the 255 per-stem `schedules/<stem>/`
subtrees (the IDFs reference `../../schedules/<stem>/…`, resolved from `<FLEET_DIR>/out/<stem>/`).
Shipped to `/speed-scratch/o_iseri/fleets/EU11_GB-LDN-RECOVERY-2026-09-07`; remote verification
`idfs=255 sched=255 fleet=255`.

Submission: `sbatch --array=1-255%32 --time=7-00:00:00 --partition=ps --job-name=eu11_ldn_recovery
--export=FLEET_DIR=/speed-scratch/o_iseri/fleets/EU11_GB-LDN-RECOVERY-2026-09-07 submit_fleet.sbatch`
→ **job `1310803`**. Walltime and partition set on the CLI, never from the shared `.sbatch` (which bakes
`--time=01:30:00`). Dispatch confirmed placed, not assumed: 32 RUNNING account-wide, remainder
`PENDING (JobArrayTaskLimit)` at the full `%32` cap.

**Known limitation, recorded before the results exist.** These 255 IDFs were emitted by the **pre-fix**
cutter — before `D-EU-109` T03 (ring cleanup) and `D-EU-107` T03 (`C12` balance) land. 9 of the 255 already
carry the discard defect (`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` 7,
`FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` 2) and the remaining 246 are exposed to the same
imbalance the `C12` gate exists to remove. So T06's EUIs are **provisional**: they are the correct answer
for today's engine and will be superseded, for at least those 9 and for any of the 246 whose plate the
`C12` gate re-scores, by the merged re-emission. The merged wave's scope is unchanged by this run — those
255 stems are re-emitted there like every other London building, and the T07 restatement must be redone
after it. Nothing published from T06 may be quoted as final London EUI.

Test status: no test run (director submission task; the gate is T07's harvest).
