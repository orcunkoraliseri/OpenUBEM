# PLAN — `eu-nocore-interzone-rootcause` — why `intersect_match` throws away 1,306 no-core dwelling layouts

**Slug:** `eu-nocore-interzone-rootcause` · **Opened:** 2026-09-04 · **Director:** this session · **Executor:** fresh Sonnet
**Specs (read-only):** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v5.md` §3 `FINDING 249`
(lines 537-609) and §4 `D-EU-99` (this plan's authorisation).
**Predecessor:** `PLAN_eu-engine-nocore-carryin-2026-09-03.md`, T05, `CP-2` **FAILED** — not closed, this plan
does not reopen it, it feeds a re-audit of its own fifth gate.
**Owner authorisation (verbatim, 2026-09-04):** *"ok then prepare investigation plan to solve 5th gate for
CP-2, and then start execution"* — given in reply to the one open decision left after the `CP-2` audit,
`D-EU-99` (root-cause `intersect_match` before any campaign). A second message, same session:
*"i want to handle this one and submit the simulations on the speed, we are close to 95% for each
neighbourhood, in Madrid we already pass 95% threshold, we are ready to go, solve this last pass of CP-2, and
start simulations"* — the 95 % coverage bar is already cleared (`D-EU-91`/`D-EU-96`); this pre-authorises the
Speed submission itself, contingent on `CP-2` re-passing, mirroring `D-EU-98`'s pattern. Both taken as
`D-EU-99`.

---

## 1. Why this plan exists

`CP-2`'s fifth gate — that the emitted IDFs actually carry the no-core dwelling layouts — fails on 1,306 of
2,262 emitted-family buildings (57.7 %). `FINDING 210`'s existing safety net
(`find_mismatched_interzone_pairs` + `_force_reroute_room_layout_to_one_zone_per_floor`,
`scripts/run_eu_s2_campaign.py::build_idf_for_building`) fires and silently discards the dwelling layout,
because geomeppy's `intersect_match` cannot resolve interzone vertex mismatches on the finer no-core
subdivision. Real dwelling layouts fall **1,446 → 956** even though the new cutter divides 831 more plates
than the core-era logic ever could. Full record: `STATE_european_locations_v5.md:537-609`.

Two building-level probes already run for `FINDING 249` (Madrid, `k = 1` share, median `k`, footprint
vertices, storeys, reflex vertices, rectangularity) **found no separation** between rerouted and clean
buildings. `STATE_european_locations_v5.md:591-595` is explicit that the next task is *inside*
`intersect_match`'s vertex handling, not the cut geometry, and is explicit that it is **not** a threshold
move and **not** a relaxation of `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`.

**This plan tests one specific, code-grounded mechanism the two prior probes never touched**, and only after
it is confirmed or refuted does it move to a remedy:

`generate_european_building_dwelling_layout` (`openubem/geometry/european_residential.py:2639-2718`) calls
`_layout_for(count)`, cached **only by the per-floor dwelling count** (line 2664-2684). Two floors with the
*same* count reuse the identical cached cut and stay perfectly aligned. Two floors with *different* counts —
grouped separately as consecutive-equal-count `EuropeanStoreyGroup`s, line 2686-2698 — get two independently
computed calls to `cut_storey_nocore` (`openubem/geometry/european_nocore.py:1751-1777`), each cutting the
same footprint into a different number of unrelated pieces. Nothing in either function makes the two
partitions align. At every such transition the ceiling rings of the top zones in group N and the floor rings
of the bottom zones in group N+1 come from two structurally unrelated cuts, which is exactly the
"independently, for the ceiling of storey n and the floor of storey n+1" divergence the `FINDING 210`
root-cause pass already documented in `intersect_match` (`docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791`).
The core-era regime carried a stable circulation-carrying scheme across most of a building's floors; no-core
has no such stabiliser, so every dwelling-count change is a potential mismatch site — a plausible, and
previously untested, explanation for why the reroute rate went from 2 buildings to 1,306.

**This plan's job is to confirm or refute that mechanism, and only on confirmation, design and validate a
remedy that stops discarding the dwelling layout at those transitions — without touching the accepted cutter
or the non-editable shared surfaces module.** It is not a threshold move and not a tolerance relaxation.

---

## 2. Hard rules for the executor — non-negotiable

1. 🔴 **`openubem/idf/surfaces.py` stays non-editable** (`D-EU-41`). Any remedy is a European-only wrapper in
   `scripts/run_eu_s2_campaign.py`, the exact pattern `FINDING 210`'s own fix already used.
2. 🔴 **The accepted no-core cutter is frozen.** Never edit `openubem/geometry/european_nocore.py`'s cutting
   logic (`cut_storey_nocore`, `build_flats`, or anything it calls) and never edit
   `scripts/eu21/07_nocore_tests.py`/`01`-`06`/`08` (`D-EU-95`, bit-parity with `_r5`). A remedy may only
   change how storeys that were *already* cut are **assembled and matched across floors** in the IDF builder —
   never how one storey is cut.
3. 🔴 **No threshold move.** `NEAR_DUPLICATE_VERTEX_TOLERANCE_M` (0.005), `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG`
   (0.1) and `MAX_FLAT_ASPECT` (2.5) are not touched by this plan, per `STATE_european_locations_v5.md:594-595`.
4. 🔴 **No EnergyPlus run on Speed before `CP-2` (T04).** Local Windows EnergyPlus 23.1.0 only
   (`C:\EnergyPlusV23-1-0\energyplus.exe`), matching the `FINDING 210` root-cause pass's own standard: a raw
   `find_mismatched_interzone_pairs` pass is not sufficient proof, only a real `RC=0`/`0 Severe`/`0 Fatal` run
   is. T06's Speed submission (director-only, after `CP-2` is re-signed) is the one exception — `sbatch --array`
   only, `--time=7-00:00:00` minimum on the CLI, never on the login node, `_ssh()` helper for every remote
   command (`D-EU-99` clause 2, mirrors `D-EU-98`).
5. 🔴 **`CP-1` (after T02) gates any code change.** The executor characterizes and reports; the director
   confirms the mechanism and picks the remedy shape before any file outside a new diagnostics script is
   touched. Do not implement a fix ahead of `CP-1`.
6. **Never regenerate or overwrite a delivered artifact** (`D-EU-85`) — `openubem/outputs/eu_evidence/EU-11/
   <DISTRICT>_nocore_2026-09-03/` and `EU-21/engine_parity/idf_audit_2026-09-03.json` are read-only inputs to
   this plan; new artifacts get a new dated path.
7. **Never `git add`/`commit`/`stash`/`restore`/`checkout`/`reset`/`clean`.** The dirty tree is the owner's.
8. **Never write into `EU-17/` or `EU-20/`.** Do not edit root `main.py`, OVERVIEW or DESIGN docs. No `.py`
   files under `docs/`, ever.
9. **Before debugging any error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` first** — `FINDING
   210` and `FINDING 249` are both already there. **After solving any error, register it there** before closing
   the task.
10. If the plan and the code disagree, **stop and quote the conflict**. Do not invent a resolution.

---

## 3. File layout

| path | action |
| --- | --- |
| `scripts/eu21/11_interzone_diagnostics.py` | **new** — T01/T02 characterization: storey-group transition counts per building, stratified sampling, raw `find_mismatched_interzone_pairs` capture. |
| `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/` | **new** — diagnostic + validation artifacts (JSON), dated. |
| `scripts/run_eu_s2_campaign.py` | **edited at `CP-1`, not before** — the remedy the director picks at `CP-1`, scoped to `build_idf_for_building` (lines 442-627) exactly as the `FINDING 210` fix was. |
| `openubem/geometry/european_nocore.py`, `european_residential.py` | **read-only** — the storey-group cache/grouping (lines 2664-2698) is read for T01, never edited. |
| `openubem/idf/surfaces.py` | **read-only** (`D-EU-41`). |
| `scripts/eu21/07_nocore_tests.py`, `01`-`06`, `08` | **read-only** (`D-EU-95`). |
| `tests/geometry/`, `tests/test_eu*.py` | **edited only where §6 T04 names them.** |
| `openubem/outputs/eu_evidence/EU-11/*_nocore_2026-09-03/` | **read-only** — the source of the 1,306 rerouted `building_id`s (`prepared_buildings.csv`, `geometry_outcome` column). |

---

## 4. Dependency decisions (pinned)

1. No new third-party dependency. `shapely` and `geomeppy` are already vendored; the diagnostics script uses
   only them plus `pandas` (already used by `prepared_buildings.csv` readers elsewhere in `scripts/eu21/`).
2. `11_interzone_diagnostics.py` imports from `openubem/` only (`generate_european_building_dwelling_layout`,
   `cut_storey_nocore`) and reads existing CSV/IDF artifacts on disk — it never calls
   `scripts/eu21/07_nocore_tests.py` or re-cuts a plate through the test harness (`D-EU-95` still applies to
   any code path that could touch the accepted cutter's own call surface).
3. Per-building `floor_allocations` (the per-floor dwelling counts driving `generate_european_building_
   dwelling_layout`) are re-derived from the same census inputs `scripts/eu21/10_engine_census.py` (`T05a`)
   already used — never invented or approximated from the IDF alone, since the IDF of a *rerouted* building no
   longer carries the per-floor counts that produced the mismatch.
4. The remedy, once picked at `CP-1`, lives entirely inside `scripts/run_eu_s2_campaign.py` — no new module —
   unless `CP-1` explicitly authorises one; default to extending the existing gate function.

---

## 5. DESIGN facts, with citations

1. **The `CP-2` fifth-gate failure, in full**, including the two probes that found nothing:
   `STATE_european_locations_v5.md:537-609`.
2. **The reroute gate itself** — `find_mismatched_interzone_pairs` + `at_risk` branch + reroute +
   post-reroute repair chain (`_repair_roof_roof_pairs`, `_repair_mismatched_horizontal_pairs`,
   `_pair_interfloor_surfaces`) + the T15/`D-EU-58` disclosed-tolerance branch:
   `scripts/run_eu_s2_campaign.py:486-556`.
3. **`find_mismatched_interzone_pairs`** — pairs surfaces by `Outside_Boundary_Condition_Object`, compares raw
   vertex counts only: `openubem/idf/surfaces.py:547-571`.
4. **`_force_reroute_room_layout_to_one_zone_per_floor`** — collapses the *whole* building's `room_layout`/
   `european_dwelling_layout` zones to one massing zone per floor when triggered; explicitly documented as
   reusing the same safety net for both regimes rather than getting its own: `openubem/idf/surfaces.py:640-706`.
5. **The candidate mechanism** — `_layout_for(count)` cached only by dwelling count, `EuropeanStoreyGroup`s
   formed only from consecutive *equal*-count floors, each distinct count an independent
   `cut_storey_nocore`/`generate_european_nocore_storey_layout` call with no cross-floor alignment:
   `openubem/geometry/european_residential.py:2639-2718` (cache/grouping at 2664-2698),
   `openubem/geometry/european_nocore.py:1338-1360` (`generate_european_nocore_storey_layout`) and
   `:1751-1777` (`cut_storey_nocore`).
6. **`FINDING 210`'s root-cause pass** — `intersect_match` computes new boundary vertices independently per
   surface, confirmed to reproduce cross-block (not only same-label) pairs, and confirmed downstream of ring
   construction (no ring-builder change can fix it):
   `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791`.
7. **`D-EU-41`** — `openubem/idf/surfaces.py` is non-editable; the precedent fix pattern is a European-only
   wrapper pass in `scripts/run_eu_s2_campaign.py`: `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:596-598`.
8. **`D-EU-95`** — the no-core cutter is copied, never re-implemented or tuned; any behavioural difference
   from `_r5` is a defect of a plan, not an improvement: `PLAN_eu-engine-nocore-carryin-2026-09-03.md` §1.
9. **The per-building reroute labels** live in `geometry_outcome` in each district's
   `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_nocore_2026-09-03/prepared_buildings.csv`
   (`DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` for the 1,306); the audit JSON
   (`openubem/outputs/eu_evidence/EU-21/engine_parity/idf_audit_2026-09-03.json`) carries only the aggregate
   `geometry_outcome_counts` per district, not a building-id list — T01 must join against the CSV.

---

## 6. Task list

### T01 — Storey-group transition census: does the mechanism separate the groups?

**What.** For every one of the 2,262 emitted-family buildings in the four rebuilt district trees, compute the
number of `EuropeanStoreyGroup` transitions (count of times the per-floor dwelling count changes between
consecutive floors), using the same `floor_allocations` `scripts/eu21/10_engine_census.py` derived for `T05a`.
Cross-reference against each building's `geometry_outcome` in `prepared_buildings.csv` (rerouted vs. real vs.
massing-fallback). Write one row per building to
`openubem/outputs/eu_evidence/EU-21/interzone_rootcause/T01_transition_census_2026-09-04.csv`
(`building_id`, `district`, `n_floors`, `n_groups`, `n_transitions`, `geometry_outcome`).

**Why.** The two prior `FINDING 249` probes tested whole-footprint shape stats and found no separation. This
tests a specific, code-grounded structural property (§1, §5.5) neither probe touched. If transition count
does not separate rerouted from real either, the hypothesis is refuted here, cheaply, before any deeper work.

**How.** New script `scripts/eu21/11_interzone_diagnostics.py`, function `census_transitions(district)`. Do
not re-run the cutter — call `generate_european_building_dwelling_layout` with the already-known
`floor_allocations` per building (same inputs `T05a`'s census used) and read `len(storey_groups) - 1` for the
transition count. Report, per district and pooled: reroute rate at `n_transitions == 0` vs. `n_transitions >= 1`,
and (if the pooled counts support it) a simple rate-by-transition-count table.

**How to test.** No unit test — this is a one-off census over real data, same as `T05a`/`FINDING 246`. Sanity
check: `n_groups` must sum consistently with the already-known `t05a_EMITTED`/`REFUSED_K_GT_12`/`FALLBACK`
counts per district (`idf_audit_2026-09-03.json`); a building's `n_floors` must match its record in the
census input. Report the two sanity totals in the progress log, not just the correlation.

### T02 — Confirm the mechanism at the surface level, on a stratified sample

**What.** Pick a stratified sample of ~40 buildings (roughly 10 each: reroute×transitions, reroute×no-transitions,
real×transitions, real×no-transitions — adjust cell sizes to what T01's table actually supports). Rebuild each
locally (`build_idf_for_building`, before the reroute gate fires — instrument it to capture
`find_mismatched_interzone_pairs`'s raw output pre-gate for every building, including ones that pass clean).
For every mismatched pair found, determine whether the two surfaces belong to zones on either side of a
storey-group transition (compare each zone's `_F<n>` floor index against the building's own transition floor
indices from T01) or are within one group. Write per-building detail to
`openubone/outputs/eu_evidence/EU-21/interzone_rootcause/T02_mismatch_detail_2026-09-04.json`.

**Why.** T01 shows correlation at best; T02 shows whether the actual mismatched surface pairs sit exactly
where the hypothesis predicts (across a transition) or scattered elsewhere (which would refute it even if T01
correlates, e.g. if some third factor drives both).

**How.** Extend `11_interzone_diagnostics.py` with `sample_and_probe(...)`. Reuse `build_idf_for_building`'s
own zone list and `find_mismatched_interzone_pairs`, called the same way `scripts/run_eu_s2_campaign.py:516`
already does, but capture the result instead of acting on it (do not call the reroute here — this task only
observes). Fix the path typo in this task's own filename before writing it (`openubone` above is this plan
doc's typo, not an instruction — write to `openubem/...`).

**How to test.** No unit test. Report, in the progress log: of all mismatched pairs found across the sample,
what fraction cross a group transition vs. sit within one group; and separately, of buildings with zero
transitions, whether any still mismatch (if so, the mechanism is necessary but not sufficient, and that must
be said plainly, not smoothed over).

### T02b — Rebuild the T02 sample from real production geometry (network-safe districts only)

**What.** T02 as run (progress log above) found **0** mismatched pairs across all 40 sampled buildings,
including all 20 real `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` buildings — `label_agreement`
20/20 **disagree**. This is not a negative result; it means T02's census-derived `floor_allocations`
reconstruction (dependency decision 3) does not reproduce what production actually built for the very
buildings under test, so T02 tested nothing. Because T01's `n_dwelling_count_changes` classification is
computed from that **same** reconstruction (dependency decision 3 applies to both tasks), T01's "weak
separation" finding (§8 T01 notes) is only as trustworthy as this reconstruction — and it is now shown
unreliable for exactly the reroute cohort that matters. Pick ≥15 real-labelled buildings — reroute and
clean, roughly half each — from **`ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`
only** (Bologna excluded: its `_geometry()` path makes live HTTP calls, forbidden). For each, call the
**real** `run_eu_s2_district_campaign.py::prepare()`/`_geometry()` path directly (not the census
reconstruction) to get the building's actual `floor_allocations`, build its zones, and run
`find_mismatched_interzone_pairs` pre-gate exactly as T02 did. Diff each building's real `floor_allocations`
against what T01/T02's census reconstruction produced for the same `building_id` (already in
`T01_transition_census_2026-09-04.csv`).

**Why.** Establishes whether the reconstruction is wrong (and how — different per-floor split from the same
totals, or different totals/storeys entirely) before either accepting or rejecting T01/T02 as evidence for
`D-EU-99` clause 3. This is still diagnosis, not remedy — no file outside `11_interzone_diagnostics.py` and
its output directory is touched.

**How.** Extend `11_interzone_diagnostics.py` with a new function that imports `prepare`/`_geometry` from
`scripts/run_eu_s2_district_campaign.py` (already read at lines 1-230, 330-460 per T01/T02) and calls them
directly for the picked `building_id`s only — do not run the full district campaign. Reuse T02's own
`find_mismatched_interzone_pairs` capture code.

**How to test.** Report, per picked building: real `floor_allocations` vs. reconstructed `floor_allocations`
side by side, whether they differ and how (remainder-floor placement, total dwelling count, `storeys` value,
or something else), and the real-geometry `find_mismatched_interzone_pairs`/`label_agreement` result on this
corrected sample (does it now agree with `prepared_buildings.csv`'s real reroute label?). If real and
reconstructed `floor_allocations` are identical for these buildings, say so plainly — that would point the
divergence at something *other* than `floor_allocations` (e.g. footprint geometry itself, vertex ordering),
and `CP-1` must be told that instead.

### T02c — Capture the full `at_risk` condition, not just `mismatched`

**What.** T02 and T02b both captured only `find_mismatched_interzone_pairs` (`mismatched`), but the real gate
(DESIGN fact 2, `scripts/run_eu_s2_campaign.py:517`) is `at_risk = mismatched or
_has_near_duplicate_vertex_surfaces(idf)` — an OR of two independent heuristics. The code's own comment at
lines 502-515 states a *confirmed* (not hypothesised) mechanism for the second heuristic: `intersect_match`
inserts a sub-mm near-duplicate vertex asymmetrically into two paired surfaces' own rings, which
`find_mismatched_interzone_pairs`'s raw vertex-count check cannot see but `_has_near_duplicate_vertex_surfaces`
catches proactively; a further comment (lines 530-548, referencing a pre-no-core `T14`/`T15` investigation
under the old core/ruled regime, `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` /
`PLAN_eu21-group-schemes-2026-09-01.md`) states that in that population, `mismatched` almost never fired —
only the near-duplicate-vertex heuristic did. T02b's own 16-building real-geometry sample is consistent with
this: `find_mismatched_interzone_pairs=0` on all 16, including 5 real reroute-labelled buildings. Re-probe the
**same T02b 16-building real-geometry sample** (reuse its already-built zones/IDFs, do not rebuild) and this
time also capture `_has_near_duplicate_vertex_surfaces(idf)`. Report, per building: `mismatched`,
`near_duplicate_vertex`, `at_risk`, and whether `at_risk` now agrees with the building's real
`geometry_outcome` label.

**Why.** If `near_duplicate_vertex` is what actually trips `at_risk` for the reroute-labelled buildings in
this sample (as the pre-no-core precedent and T02b's own zero `mismatched` count both suggest), then the
mechanism this plan must root-cause is **not** the per-floor-count-cache/`EuropeanStoreyGroup` hypothesis
(`D-EU-99` clause 3) at all — it is why `intersect_match` inserts that sub-mm near-duplicate vertex pair in
the no-core geometry so much more often than it did under core (2 buildings → 1,306). `CP-1` needs this
before picking a remedy shape, because a remedy aimed at the wrong heuristic fixes nothing.

**How.** Extend `11_interzone_diagnostics.py`'s T02b function (or add a small sibling) to call
`_has_near_duplicate_vertex_surfaces` from `openubem/idf/surfaces.py` (read-only import, not edited) on the
same 16 real-geometry IDFs/zone lists T02b already built. If reusing the in-memory objects is impractical,
rebuild only these 16 (already known to be network-safe, ES-MAD-BERRUGUETE/FR-LYO-HAUTCOEURPENTES/GB-LDN-STDUNSTANS
only) rather than the full fleet.

**How to test.** Report the per-building table (`mismatched`, `near_duplicate_vertex`, `at_risk`,
`real_label`) for all 16, and the aggregate: how many of the 5 real-reroute buildings have `at_risk=True` now
(vs. 0/5 before this task), and how many of the 11 real-clean buildings have `at_risk=False` (should stay
11/11 if the heuristic is precise). If `at_risk` still disagrees with `real_label` for some buildings, say so
plainly — do not round to "confirmed."

### `CP-1` — Director confirms or refutes the mechanism, picks the remedy shape

**Stop and report here, before touching any file outside `scripts/eu21/11_interzone_diagnostics.py` and its
own output directory.** Present T01's table, T02's per-pair breakdown, T02b's real-vs-reconstructed
`floor_allocations` diff, and T02c's `at_risk` split. The director:
- confirms the transition mechanism, refutes it, or narrows it (e.g. "necessary but not sufficient — also
  needs condition X" if T02 shows within-group mismatches too);
- if confirmed, picks one remedy shape from the candidates below (or another, but must state it explicitly —
  the executor does not choose): (a) proactively pre-split each transition's shared boundary into the true
  set of overlap polygons between the two differing partitions before `extrude_geometry`/`intersect_match`
  ever run, so the two rings are already congruent going in; (b) scope
  `_force_reroute_room_layout_to_one_zone_per_floor`'s reroute to only the storey pair at the mismatched
  transition (partial reroute), preserving dwelling zones on every other floor instead of collapsing the whole
  building; (c) something else the director specifies.
- if refuted, this plan stops at `CP-1` and reports back to the owner — no further task runs.

### T03 — Implement the picked remedy (runs only after `CP-1` authorises it)

**What.** Implement exactly the remedy `CP-1` picked, inside `scripts/run_eu_s2_campaign.py::build_idf_for_building`
(lines 442-627), following the `FINDING 210` fix's own pattern (a European-only wrapper, `openubem/idf/
surfaces.py` untouched).

**Why.** `CP-1` is the ambiguity-resolution point (hard rule 5/10) — the remedy shape is an architectural
choice with real trade-offs (simulation fidelity vs. implementation cost), not something to infer.

**How.** As directed at `CP-1`. Do not widen `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`/`COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG`
as part of this — if the picked remedy turns out to need a tolerance change, stop and report that back rather
than making it inside this task.

**How to test.** New tests under `tests/test_eu_s2_campaign.py` (or a new `tests/geometry/test_eu99_interzone_*.py`
if the remedy is geometry-level, named per hard rule 8's read-only list) proving the remedy on a synthetic
two-transition building, plus the existing test suite must not regress (`pytest -q -n 8 tests/`).

### T04 — Validate the remedy on the T02 sample with real EnergyPlus

**What.** Rebuild the same ~40-building T02 sample with the remedy in place. For every one, run local
EnergyPlus 23.1.0 (`ExpandObjects` + `energyplus.exe`, matching `submit_fleet_t08.sbatch`'s own invocation,
same standard as the `FINDING 210` root-cause pass) — not only the Python heuristic. Report `RC`/severe/fatal
counts and, for the previously-rerouted buildings in the sample, whether they now carry `_dwelling_` zones.

**Why.** `find_mismatched_interzone_pairs` returning clean was already shown insufficient once
(`e21bec78b937acf5`, `DEBUG_REFERENCES_european_locations.md:1791`) — a heuristic pass is not proof.

**How to test.** `0` Fatal / `0` Severe on all sampled buildings is the pass condition. Any failure is reported
in full (stem, error text), not silently retried with a widened tolerance.

### `CP-2` — Director signs off the validated remedy before any full rebuild

Stop and report T04's results. Director decides whether to proceed to T05 or send the remedy back to T03.

### T05 — Full four-district rebuild and `CP-2` (parent plan) re-audit

**What.** Rebuild all four districts' IDFs with the remedy (same districts, same procedure T05 of
`PLAN_eu-engine-nocore-carryin-2026-09-03.md` used), to a new dated output directory. Re-run that plan's own
gate-5 check (real dwelling layouts vs. reroute count vs. the delivered core-era build) and report the same
five-gate table this plan's §1 quotes.

**Why.** This is the actual finish line: does the fifth `CP-2` gate now pass.

**How.** Reuse `scripts/run_eu_s2_district_campaign.py::prepare` unmodified except for whatever T03 changed in
`build_idf_for_building`; do not touch district-campaign logic beyond that.

**How to test.** Same five checks `FINDING 249`'s table used (`STATE_european_locations_v5.md:561-567`), on
the new rebuild vs. the delivered core-era build. Report the gate-5 numbers explicitly — do not just say
"improved."

**If gate 5 fails**, this plan stops here and reports back — no submission, `T06` does not run.

### T06 — Build and submit the Speed campaign (director only, after gate 5 passes)

**What.** Package the four districts' rebuilt fleets (T05's output) and submit to Speed, exactly as
`D-EU-98` ran the pre-`FINDING 249` submission.

**Why.** `D-EU-99` clause 2 pre-authorises this, contingent only on `CP-2` re-passing — the owner's own
verbatim instruction this session, mirroring the established `D-EU-98` pattern.

**How.** Director-only, not the executor. `sbatch --array`, fire-and-forget, `--time=7-00:00:00` minimum on
the CLI (never baked into the shared `.sbatch`), `_ssh()` helper for every remote command
(`scripts/cluster/t08_harvest_results.py:104`, remote shell is tcsh). Confirm `squeue -u o_iseri` is clear of
this arc's jobs before submitting; never touch another project's runs. Update
`prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` with the job ids and CP-2 outcome after
submission, not before — same order `D-EU-98` used.

**How to test.** `sacct`/`squeue` confirms the array is queued/running. Harvest and results are a follow-up,
not this task.

---

## 7. Stop-and-report points

1. **`CP-1`** (after T02c) — mechanism confirmed/refuted, remedy shape picked or plan stopped. Director only.
2. **`CP-2`** (after T04) — remedy validated on the sample with real EnergyPlus, or sent back to T03. Director only.
3. **Gate-5 re-audit** (after T05) — pass → director proceeds straight to T06 (pre-authorised, `D-EU-99`
   clause 2); fail → plan stops and reports, no submission.

---

## 8. Progress log

#### T01 — Storey-group transition census: does the mechanism separate the groups? — completed 2026-09-04

**Artifacts:**
- `scripts/eu21/11_interzone_diagnostics.py` (new) — `census_transitions()`, `_classify()`, `_load_census_universe()`.
- `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/T01_transition_census_2026-09-04.csv` — 2,544 rows (all four districts, every `EU-20/morphology_census.csv` building).

**Deviations:**
- 🔴 **Plan/code conflict, quoted per hard rule 10** (also documented in `11_interzone_diagnostics.py:1-38`): §6 T01 "What" defines the diagnostic in English as "the number of times the per-floor dwelling count changes between consecutive floors." §6 T01 "How" instead says to read it as `len(storey_groups) - 1`. These are not the same quantity. `generate_european_building_dwelling_layout` (`openubem/geometry/european_residential.py:2686-2698`) appends one `EuropeanStoreyGroup` per non-absorbed floor **unconditionally** — it never merges two consecutive equal-count floors into one group; only the `_layout_for` cache (line 2673-2684) reuses the same layout *object* across equal-count floors, the `storey_groups` list itself still carries one entry per floor. Verified empirically (synthetic 4-storey building, per-floor counts `[3, 3, 2, 2]`): 4 `storey_groups` returned, `len(storey_groups)-1 == 3`, while `count[i] != count[i-1]` is true only once. `len(storey_groups)-1` is therefore `n_floors - 1` for nearly every AB building regardless of whether any dwelling count ever changes, and does not test the mechanism §1 describes. Not resolved unilaterally: both quantities are computed and reported as separate CSV columns — `n_transitions` (literal "How" formula) and `n_dwelling_count_changes` (the "What"/§1 semantic quantity). Neither is treated as authoritative; CP-1 decides.

**Test status (sanity checks, plan-required):**
- Sanity 1 — `engine_status` (EMITTED/REFUSED_K_GT_12/FALLBACK) vs T05a's own `openubem/outputs/eu_evidence/EU-21/engine_parity/engine_census_2026-09-03.json`: matches exactly in all four districts (905/9/47, 280/3/14, 62/13/7, 1032/0/172); `fleet_match=True`.
- Sanity 2 — `n_floors` vs census input: `n_floor_mismatches=0/2544`, `n_missing_geometry=0/2544`.

**Notes:**
- Pooled reroute-rate-by-`n_transitions` (literal, emitted-family n=2,262, rerouted=1,306): `n_transitions==0` → 45.2% (103/228); `n_transitions>=1` → 59.1% (1203/2034). Rises roughly monotonically through the middle bins (0.45→0.54→0.57→0.54→0.63→0.65→0.63→0.64) with noise at the sparse tails (n<20).
- Pooled reroute-rate-by-`n_dwelling_count_changes` (semantic, binary in practice — `allocate_european_dwellings`'s `divmod` remainder allocation produces at most one count change per building): `0` changes → 53.8% (238/442); `1` change → 58.7% (1068/1820).
- 🔴 Under the semantically-correct metric (`n_dwelling_count_changes`, matching §1's own mechanism description), separation is weak: buildings where every floor shares the identical dwelling count (so `_layout_for`'s cache reuses the exact same layout object on every floor, by construction — no two independently-cut partitions ever meet) still reroute at 53.8%, barely below the 58.7% for buildings with an actual count change. This weighs against the count-change/independent-cut mechanism (§1, `D-EU-99` clause 3) being the dominant driver — if it were, the zero-change group should sit near 0%, not 53.8%.
- Full per-district tables (both metrics): `t01_run.log` (scratchpad) and `T01_transition_census_2026-09-04.csv`. Wall time 2,119.8 s.

#### T02 — Confirm the mechanism at the surface level, on a stratified sample — completed 2026-09-04

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/T02_mismatch_detail_2026-09-04.json` — 40-building stratified sample (10 per cell: `reroute_transitions`, `reroute_no_transitions`, `real_transitions`, `real_no_transitions`, using `n_dwelling_count_changes` as "transitions" per T01's finding above).
- `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/t02_idfs/<district>/<stem>/<stem>.idf` — 40 locally-rebuilt pre-gate IDFs.

**Deviations:**
- Zones built from census-derived `floor_allocations` (same source as T01, dependency decision 3 — `archetype_id="engine_census_T05a"`, `building_type="AB"`, EU-20 `dwellings_total`/`storeys`), **not** from `run_eu_s2_district_campaign.py::_geometry`'s production TABULA-mapping pipeline, because that pipeline makes live HTTP calls for Bologna (`_it_rows`, `opendata.comune.bologna.it`) — forbidden by CLAUDE.md "No live-network integration tests until §5.3 is unblocked." `context` is passed as `[]`: `apply_adiabatic_party_walls`, its only consumer inside `build_idf_for_building`, runs at `scripts/run_eu_s2_campaign.py:557`, strictly after the line-516 `find_mismatched_interzone_pairs` call this task captures, so it cannot affect the result being observed.
- 🔴 **This substitution does not reproduce the real mismatch.** `find_mismatched_interzone_pairs` returned **0** mismatched pairs across all 40 sampled buildings, including all 20 buildings labeled `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` in the real `prepared_buildings.csv`. `label_agreement` (`rerouted_label == locally_mismatched`) = 20 agree / **20 disagree**, and every disagreement is a "reroute"-stratum building the local rebuild found clean. `crossing_fraction` is therefore `null` (0/0 pairs to classify) and `zero_transition_buildings_still_mismatched_count=0` is vacuous (nothing mismatched at all). `extrude_geometry` logged `"intersect_match raised ZeroDivisionError/IndexError -- purging and retrying with match() alone"` 4 times across the 40 builds (an existing resilience path inside `openubem/idf/surfaces.py`, not written by this task, not investigated further).

**Test status:**
- No unit test (per plan). Script ran to completion for 40/40 sampled buildings, 0 exceptions, 0 `"note"` (conflict) entries in the JSON.

**Notes:**
- Numbers as run: `total_mismatched_pairs_in_sample=0`, `crossing_dwelling_count_change_transition=0`, `within_one_group=0`, `crossing_fraction=null`, `zero_transition_buildings_still_mismatched=[]` (count 0), `label_agreement={agree: 20, disagree: 20}`.
- 🔴 **T02 as executed does not confirm or refute the transition mechanism at the surface level.** The census-derived zone reconstruction never reproduces any interzone mismatch, so no mismatched pair exists to classify against a transition boundary either way. This is a methodology gap — census-derived `floor_allocations` evidently diverge from whatever `_geometry()`'s production pipeline actually used for at least the 20 sampled reroute buildings (root cause not investigated further, out of scope under `CP-1` gating) — not evidence for or against the hypothesis. Flagged for the director at `CP-1`.

#### T02b — Rebuild the T02 sample from real production geometry (network-safe districts only) — completed 2026-09-04

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/T02b_real_geometry_diff_2026-09-04.json` — 16 buildings (8 reroute-labelled + 8 clean-labelled, `ES-MAD-BERRUGUETE`/`FR-LYO-HAUTCOEURPENTES`/`GB-LDN-STDUNSTANS` only).
- `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/t02b_idfs/<district>/<stem>/<stem>.idf` — 16 locally-rebuilt pre-gate IDFs, built from the **real** `run_eu_s2_district_campaign.py::_geometry()`/`_mapped_rows`/`_gb_rows` path (`11_interzone_diagnostics.py`, `_district_rows_for_mapping`/`t02b_real_geometry_diff`).
- `scripts/eu21/11_interzone_diagnostics.py` extended: `_extrude_and_find_mismatches` (factored out of T02's `_probe_building`, shared by both), `_district_rows_for_mapping`, `t02b_real_geometry_diff`, `--t02b-only` CLI flag.

**Deviations:** none from `T02b`'s spec — Bologna excluded as directed; run as an ordinary foreground call, no backgrounding.

**Test status:**
- `n_sampled=16`, `n_errors=0` — every picked building resolved in the real mapping rows, `_geometry()` and `extrude_geometry`/`find_mismatched_interzone_pairs` ran without exception.

**Notes — real vs. reconstructed `floor_allocations` diff:**
- `floor_allocations_diff = {identical: 12, different: 4}`. The 4 differences are all the same pattern: the district's real `02_residential_manifest.gpkg` `levels` gives **1 real storey** (`_geometry()`'s actual zones: a single `[1]`-dwelling group), while `EU-20/morphology_census.csv`'s `storeys` field the T01/T02 reconstruction used gives 2 or 3 storeys for the identical `building_id` (recon `[1, 0]` / `[1, 0, 0]`, the extra floors absorbed as 0-dwelling) — `way/403642583`, `way/941927250`, `way/435449428` (all 3 reroute-labelled) and `way/941927245` (clean-labelled), all `ES-MAD-BERRUGUETE`. `storeys`/`levels` disagree between the two data sources for at least these 4/16 buildings; the census-derived floor_allocations reconstruction dependency decision 3 relies on is not always faithful.
- The remaining 12/16 have **identical** real vs. reconstructed floor_allocations, including 5 of the 8 reroute-labelled buildings (`way/435505191` `[2,2,2,2]`, `way/322742264` `[2,2,2,2]`, `way/435505194` `[3,2,2,2,2]`, `BATIMENT0000000240879996_part0` `[6,6,6,6,5,5]`, `way/942642640` `[3,2,2]`) — so the T02b divergence is not solely a `floor_allocations`-reconstruction artifact.

**Notes — corrected `label_agreement`:**
- 🔴 **Still 8 agree / 8 disagree — unchanged from T02's ratio, now on real production zones.** `find_mismatched_interzone_pairs` returned **0** mismatched pairs for **all 16** sampled buildings, including all 8 real reroute-labelled ones (both the 5 with identical floor_allocations and the 3 with a real 1-storey building). Every "agree" is a clean-labelled building (trivially: 0 mismatches, not rerouted); every "disagree" is a reroute-labelled building the local rebuild — on its **real, production-identical** zones — found clean.
- 🔴 **Likely explanation, not investigated further (characterization only, no file touched to test it):** `build_idf_for_building`'s actual reroute gate is `at_risk = mismatched or _has_near_duplicate_vertex_surfaces(idf)` (`scripts/run_eu_s2_campaign.py:517`), not `mismatched` alone. T02/T02b's `How` (and this task's own instructions) name only `find_mismatched_interzone_pairs` (`scripts/run_eu_s2_campaign.py:516`); `_has_near_duplicate_vertex_surfaces` (`scripts/run_eu_s2_campaign.py:94-120`, the near-duplicate/near-collinear-vertex heuristic `FINDING 210`'s own root-cause pass added because a raw vertex-count match is "NOT sufficient on its own", `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791`) was never called by either task. This would explain the 100% miss rate uniformly across both the floor_allocations-identical and floor_allocations-different reroute cases. Neither T02 nor T02b as specified checked it; flagged for the director at `CP-1` rather than acted on.

#### T02c — Capture the full `at_risk` condition, not just `mismatched` — completed 2026-09-04

**Artifacts:**
- `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/T02c_at_risk_probe_2026-09-04.json` — the same 16-building T02b sample (`_pick_t02b_sample`, identical seed/bucket size), now with `mismatched`, `near_duplicate_vertex`, `at_risk`.
- `openubem/outputs/eu_evidence/EU-21/interzone_rootcause/t02c_idfs/<district>/<stem>/<stem>.idf`.
- `scripts/eu21/11_interzone_diagnostics.py` extended: `_pick_t02b_sample` (factored out of `t02b_real_geometry_diff` so T02c reuses the identical selection), `t02c_at_risk_probe`, `--t02c-only` CLI flag.

**Deviations:**
- T02b never persisted the extruded `idf` objects (only the header text was written to `t02b_idfs/`, `extrude_geometry` was never followed by `idf.saveas`), so "reuse its already-built zones/IDFs" was not literally possible; rebuilt the same 16 in-process instead, per the task's own accepted fallback. Ran as an ordinary foreground call, no backgrounding.
- Factual correction to the plan text and the coordinator's dispatch: `_has_near_duplicate_vertex_surfaces` lives in `scripts/run_eu_s2_campaign.py:94`, not `openubem/idf/surfaces.py` (`grep -rn "def _has_near_duplicate_vertex_surfaces"` finds one definition, in that file). Imported from its actual location; still read-only, not edited.
- 🔴 The dispatch's aggregate framing ("5 real-reroute buildings", "11 real-clean buildings") does not match this sample: the actual T02b/T02c 16-building sample is **8 reroute-labelled / 8 clean-labelled** (verified against T02b's own `label_agreement={agree:8, disagree:8}` and the per-building list in both JSONs). Reported below using the real 8/8 split, not silently reconciled to 5/11.

**Test status:**
- `n_sampled=16`, `n_errors=0`.

**Notes — the two aggregate counts:**
- `reroute_now_at_risk = 8/8` (all 8 real reroute-labelled buildings now show `at_risk=True`).
- `clean_stays_not_at_risk = 8/8` (all 8 real clean-labelled buildings stay `at_risk=False`).

#### `CP-1` — Director confirms the mechanism, picks the remedy shape — decided 2026-09-04

**Decision — mechanism:** **Confirmed:** `near_duplicate_vertex` (`_has_near_duplicate_vertex_surfaces`,
`scripts/run_eu_s2_campaign.py:94-120`) — 16/16 real-geometry sample buildings' `at_risk` status agrees with
`geometry_outcome`, and 100% of that agreement (8/8 reroute, 8/8 clean) is carried by `near_duplicate_vertex`
alone; `mismatched` is `False` on all 16, including every reroute-labelled building. This is exactly the
pre-no-core `T14`/`T15` precedent (§6 T02c) reproduced under no-core. **Refuted:** the per-floor-dwelling-
count-cache / `EuropeanStoreyGroup` transition hypothesis, `D-EU-99` clause 3 (§1 of this plan) — consistent
with T01's own weak separation by `n_dwelling_count_changes` (53.8% vs 58.7%, §8 T01 notes) and now directly
contradicted by T02c: transitions are not where `at_risk` fires.

**Remedy shape picked — a fourth candidate, not (a)/(b)/(c) as literally worded.** Both (a) and (b) in §6
presuppose the driver sits at a storey-group *transition* boundary — refuted above. The confirmed mechanism
(code comment, `scripts/run_eu_s2_campaign.py:502-515`, EnergyPlus-verified on stem `e21bec78b937acf5`) is
vertex-level, not transition-level: `intersect_match` inserts a sub-mm near-duplicate vertex pair
*asymmetrically* into two paired surfaces' own rings (one snap-clean, one raw, ~0.0002-0.0006 m apart), which
EnergyPlus's winding-direction-dependent duplicate-vertex removal then collapses inconsistently between the
two surfaces. **Picked remedy (d):** before `intersect_match` runs, detect near-duplicate vertex pairs on each
surface (reuse `_has_near_duplicate_vertex_surfaces`'s own detection, read-only import from
`scripts/run_eu_s2_campaign.py:94-120`, do not edit `openubem/idf/surfaces.py` — `D-EU-41` precedent) and snap
each such pair to one shared coordinate, symmetrically, on **both** paired surfaces, so the asymmetry
`intersect_match`/EnergyPlus's own duplicate-removal is sensitive to never gets created. Only the
`near_duplicate_vertex`-only branch (`mismatched=False`) is in scope for this remedy — leave the existing
`mismatched=True` full-reroute path (`interzone_vertex_mismatch` reason) untouched; it is rare (0/2544 in this
plan's own sampling to date) and not characterized by this plan.

**Why this shape, not (a)/(b):** it operates at the exact granularity of the confirmed defect (a single vertex
pair) rather than a whole transition boundary or a whole storey pair, so it should touch geometry only where a
near-duplicate actually exists and leave every other dwelling zone in the building untouched — including
buildings that reroute today for reasons unrelated to any transition (T01 showed 53.8% reroute even at zero
transitions, which (a)/(b) could not have explained either). Trade-off, to be checked by T04: the snap moves
each affected vertex by up to `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`; T04 must confirm this does not regress the
`CP-2` (parent plan) area gate (currently exact 0 diff old-vs-new).

**Authorises:** T03, remedy (d) as specified above, inside `build_idf_for_building`
(`scripts/run_eu_s2_campaign.py:442-627`), `near_duplicate_vertex`-only branch. Director-picked per hard rule
5/10; not delegated to the executor.
- 🔴 **`mismatched=False` for all 16 buildings, with no exception; `near_duplicate_vertex` alone perfectly separates the sample** — `True` for exactly the 8 reroute-labelled buildings (`way/403642583`, `way/435505191`, `way/941927250`, `way/322742264`, `way/435505194`, `BATIMENT0000000240879996_part0`, `way/435449428`, `way/942642640`), `False` for exactly the 8 clean-labelled ones. `at_risk` agrees with the real `geometry_outcome` label on **16/16**. This refutes `find_mismatched_interzone_pairs`/the raw vertex-count check as the operative mechanism in this sample and points the root cause squarely at whatever makes `intersect_match` insert the sub-mm near-duplicate/collinear vertex `_has_near_duplicate_vertex_surfaces` detects (`FINDING 210`'s original, confirmed mechanism, `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791`) — not the per-floor-count-cache/`EuropeanStoreyGroup` transition hypothesis §1 set out to test (`D-EU-99` clause 3), which predicts a `mismatched` signature this sample never shows.

#### T03 — Implement the picked remedy — STOPPED 2026-09-04, not completed, no test written

**What was done before stopping:**
- Added `_symmetrize_near_duplicate_interzone_vertices` (`scripts/run_eu_s2_campaign.py`, inserted directly after `_has_near_duplicate_vertex_surfaces`, before the `PROJECTED_CRS` line) and wired it into `build_idf_for_building`'s `at_risk` branch (`scripts/run_eu_s2_campaign.py:645-661`): for the `near_duplicate_vertex`-only case (`mismatched` still `False` at that point), it re-implements `_has_near_duplicate_vertex_surfaces`'s own per-vertex math to locate every defective vertex, finds each one's closest vertex on its `Outside_Boundary_Condition_Object` partner (within `openubem/idf/surfaces.py`'s own `_COINCIDENT_VERTEX_TOL`, 0.01 m, read-only import), and snaps both to one shared coordinate via `surf.setcoords(...)` (geomeppy's own API, `.venv/Lib/site-packages/geomeppy/patches.py:39`) — preferring whichever side is already on the 1 mm precision grid as canonical. `mismatched`/`near_duplicate_vertex` are re-checked afterward; the existing reroute path is otherwise untouched, and the `mismatched=True` branch never reaches this code at all. `openubem/idf/surfaces.py` was not edited (`D-EU-41`).
- No test written yet. No `pytest` run yet. The code above is present in the working tree but not validated.

**🔴 Why stopped — empirical evidence the remedy's premise does not hold for this population.** Before writing a synthetic test, 3 of the 8 real reroute-labelled T02b/T02c buildings (`way/435505191`, `way/322742264` — `ES-MAD-BERRUGUETE`; `BATIMENT0000000240879996_part0` — `FR-LYO-HAUTCOEURPENTES`) were rebuilt via the same real `_geometry()` path T02b/T02c used, and every `BUILDINGSURFACE:DETAILED` ring was checked vertex-by-vertex with `_has_near_duplicate_vertex_surfaces`'s own math, reporting which sub-condition fires and at what value (scratchpad `probe_defect_kind.py`, not a plan artifact, throwaway). Findings, all three buildings, no exception:
  - **100% of defective vertices are the COLLINEAR sub-check (angle 179.91-179.99°), zero are the near-duplicate-proximity sub-check.** A collinear point cannot be fixed by repositioning to any coordinate on the same line — it stays exactly collinear regardless of which of the two paired values (or their midpoint) is chosen, so `_symmetrize_near_duplicate_interzone_vertices` as specified (snap, not remove) cannot clear this flag for this sub-case.
  - **Many defective surfaces carry NO interzone partner at all** — e.g. `way/435505191`'s ground `Floor` and its `Roof` both show the identical defect (`idx=3`, `angle=179.9724`) with `Outside_Boundary_Condition_Object` empty. `_has_near_duplicate_vertex_surfaces` checks every surface's own ring regardless of whether it has a partner (`scripts/run_eu_s2_campaign.py:94-125`, no partner filter); the remedy as specified ("snap... on BOTH paired surfaces") has no partner to act on for these.
  - **Where a nominal partner does exist (ceiling/floor pairs between stacked storeys of the same single-dwelling block), both sides already carry the IDENTICAL defect value** (same index, same angle, e.g. `179.9724°` on both a floor and its paired ceiling) — not the asymmetric two-slightly-different-values pattern `FINDING 210`'s own comment describes (`scripts/run_eu_s2_campaign.py:502-515`, "~0.0002-0.0006 m away"). There is nothing asymmetric to symmetrize.
  - **The defect is identical across every stacked storey of the same footprint** (`way/435505191`: `angle=179.9724` repeats bit-for-bit on the ground floor, the roof, and all three interfloor ceiling/floor pairs). This is the signature of one static footprint polygon extruded once via `add_block(num_stories=N)` (a single-dwelling, `k=1` block) carrying one inherent near-collinear vertex in its OWN ring — not `intersect_match` independently clipping two different partitions per storey and landing on two different floating-point results, which is the mechanism the remedy (and `CP-1`'s own rationale) presupposes.
  - Taken together: for this sample, `near_duplicate_vertex` is dominated by a single-ring, often-partner-less, footprint-inherent collinear vertex, not by cross-partition asymmetric insertion. Remedy (d) as literally specified (detect a pair, snap both paired surfaces to one shared coordinate) has no coordinate to change (collinear, any position on the line still collinear) and, for the partner-less surfaces, no second surface to act on at all — it would very likely resolve **0** of these 3 buildings' `at_risk` status, contradicting the goal stated at `CP-1` authorisation.

**Not decided here, per hard rule 10 ("stop and quote the conflict, do not invent a resolution") and hard rule 5 (remedy shape is director-picked, not executor-invented):** whether the actual fix should instead (i) remove/relocate the single inherent near-collinear vertex from the footprint ring itself (a different operation — vertex removal, not pair-snap — and touches a shape the accepted no-core cutter or the zone emitter produced, raising the `D-EU-41`/`D-EU-95` non-editable-boundary question afresh), (ii) special-case unpaired (no `Outside_Boundary_Condition_Object`) surfaces separately from paired ones, or (iii) something else. The `_symmetrize_near_duplicate_interzone_vertices` code already written is a correct, harmless implementation of the *pair-snap* operation as literally specified — it is left in place (not reverted, no `git` operation taken) but is not wired to be trusted, not tested, and `CP-1`'s remedy (d) is not shown to work on real data. **`pytest` was not run for this change.**

**Test status:** none. Deliberately not written — a synthetic test proving a pair-snap clears a *collinear* defect would either be unrepresentative of the real population (if constructed to only exercise the proximity sub-case) or would fail honestly (if constructed to match the real collinear/partner-less pattern above), and CLAUDE.md/plan hard rule 10 was read as blocking further work until this is resolved by the director, not smoothing over a synthetic-green result.

**Next:** reports back to the coordinator for direction before any further T03 work, new test, or `pytest` run.

#### T04 — Verify Option B's "identical pre-sim coordinates = EnergyPlus-safe" premise against stem `8cdf349a99934f0d` — completed 2026-09-04 (read-only, no code/test changes)

**What.** Director-requested narrow check, independent of T03: whether stem `8cdf349a99934f0d`'s reported `FINDING 210` ceiling/floor pair (`docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1791`, "vertex 7 of 9... interior angle of exactly 180.000000 deg") had **identical** or **asymmetric** pre-simulation `BUILDINGSURFACE:DETAILED` vertex coordinates, in a snapshot predating the 2026-08-31 collinearity-gate fix — bearing on the external Gemini report's Option B remedy (`docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_finding249_cp2-gate5-remedy-report_2026-09-04.md` §4.2), which treats coordinate identity as proof of safety.

**Snapshot selection.** Of the three candidates, only `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE/idfs/8cdf349a99934f0d.idf` (mtime 2026-08-30 18:23, i.e. before the 2026-08-31 fix) still carries real dwelling/circulation zones (`ZONE` objects: `..._F{0-3}_dwelling_{0,1,2}`, `..._F{0-3}_circulation`, 16 total). The other two (`EU-11/ES-MAD-BERRUGUETE_pre_schedule_path_fix/` mtime 2026-08-28, and `EU-17/ES-MAD-BERRUGUETE/` mtime 2026-09-01) both carry only 4 `..._F{0-3}_whole` zones — already rerouted to `one_zone_per_floor`, useless for this check (no interzone dwelling geometry left to inspect).

**Pair found.** `Block 8cdf349a99934f0d_circulation Storey 0 Ceiling 0001_4` (9 vertices, `Outside_Boundary_Condition_Object` = `Block 8cdf349a99934f0d_circulation Storey 1 Floor 0001_4`) paired with that exact floor (9 vertices, reciprocal `Outside_Boundary_Condition_Object`). Both flagged by `_has_near_duplicate_vertex_surfaces`'s own collinearity check at an interior angle of `180.0` deg — same signature as the debug-reference entry (this specific circulation shaft repeats the identical defect at every storey transition, 0/1, 1/2, 2/3, plus the unpaired ground floor and top roof; this pair was picked as the first interzone (`Outside_Boundary_Condition="Surface"`) instance).

**Finding — coordinates, verbatim (Ceiling = A, Floor = B):**
```
A (Storey 0 Ceiling 0001_4), z=3.0:
 0 (440376.908803735, 4479372.27754849)
 1 (440382.868151124, 4479380.640902955)
 2 (440376.090350857, 4479385.470425332)
 3 (440371.918850262, 4479379.616110756)
 4 (440373.952001537, 4479378.167385778)
 5 (440373.952001537, 4479378.167385777)
 6 (440373.952001537, 4479378.167385777)
 7 (440373.92547985, 4479378.130165048)   <- the ~180 deg collinear vertex
 8 (440372.164176842, 4479375.658339467)

B (Storey 1 Floor 0001_4), z=3.0:
 0 (440382.868151124, 4479380.640902955)
 1 (440376.908803735, 4479372.27754849)
 2 (440372.164176842, 4479375.658339467)
 3 (440373.92547985, 4479378.130165048)   <- the corresponding vertex
 4 (440373.952001537, 4479378.167385777)
 5 (440373.952001537, 4479378.167385777)
 6 (440373.952001537, 4479378.167385778)
 7 (440371.918850262, 4479379.616110756)
 8 (440376.090350857, 4479385.470425332)
```
B is A's ring reversed and cyclically re-started (the normal ceiling/floor mirror-winding relationship, `GlobalGeometryRules,UpperLeftCorner,CounterClockWise` per surface but opposite-facing). Matching each vertex of A to its corresponding vertex of `reversed(B)`: **all 9 pairs are equal to 9 decimal places (max distance 0.000000000 m)** — bit-for-bit identical coordinates, not merely "close." (Also visible: A/B indices 4,5,6 are themselves a near-duplicate triple, ~1e-12 apart, identically on both rings — floating-point noise from the shared construction path, not the flagged defect.)

**Conclusion — IDENTICAL, not asymmetric.** The two paired surfaces' pre-simulation input coordinates were exactly identical (once correctly wound and matched) on this pre-fix snapshot. This directly corroborates the debug reference's own reading (`OpenUBEM_debug_References.md:1791`, "EnergyPlus's convexity check legitimately drops that redundant point but not symmetrically between the ceiling and its mirrored floor") — the asymmetry documented for `FINDING 210`'s collinearity sub-case arises entirely from EnergyPlus's own internal `CheckConvexity` behaviour (winding-direction-dependent redundant-point dropping), not from any difference between the two surfaces' *input* vertex lists. 🔴 **This contradicts Option B §4.2's premise as described by the director**: "partner surfaces have identical pre-simulation coordinates" was true for this named, documented `FINDING 210` collinearity example and the building still FATALed — identical pre-sim coordinates is evidenced here to be **insufficient** proof of EnergyPlus safety for the collinear sub-case, consistent with T03's own independent finding above (a collinear point can't be fixed by repositioning, and this building's own `way/435505191`-style single-footprint circulation shaft repeats the same collinear vertex, unpaired-partner-consistent, across every stacked storey).

**Artifacts:** none new (read-only). Inspected via `geomeppy.IDF` directly against the on-disk snapshot named above; no script committed to `scripts/eu21/`, no output file written, per the dispatch's read-only scope.

**Test status:** n/a — verification only, no code/test changed, `scripts/run_eu_s2_campaign.py` not touched by this task, Option B not modified.
