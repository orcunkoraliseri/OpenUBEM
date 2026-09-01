# European locations × Step 8 — arc state (v4)

**Opened:** 2026-08-31. **Scope of v4: the floor plans.** Everything else in the arc is carried by
pointer, not restated.

🔴 **v3 is cancelled and superseded — this document is the read-first state of the arc.** Owner ruling
`D-EU-53`, 2026-08-31: the Speed runs and the v3 tasks are stopped. `STATE_european_locations_v3.md` and
`BRIEF_european_locations_v3.md` are historical from that moment; they are not executed, not appended to,
and not deleted. `prompts/DIRECTOR_PROMPT_european_locations.md` still points at v3 and must be repointed
at v4 in the next pass.

- Plain-language brief: [`BRIEF_european_locations_v4.md`](BRIEF_european_locations_v4.md)
- Arc-local error index (new, `D-EU-52`): [`debugs/DEBUG_REFERENCES_european_locations.md`](debugs/DEBUG_REFERENCES_european_locations.md)
- Rules an executor is validated against: [`rules/`](rules/) — dwelling layout, and context geometry.
- History: `previous/STATE_european_locations_v2.md`, `previous/MVP_european_locations.md`,
  `previous/WALKTHROUGH_european_locations.md`, and the superseded v3 pair in the arc root.

**This document carries current truth only.** Replace an entry when it stops being current; never append
below it.

---

## 0. Identifier bookkeeping — read before allocating anything

v4 claims **`D-EU-49` … `D-EU-53`** and **`FINDING 211` … `FINDING 214`**.
**Next free: `D-EU-54`, `FINDING 215`.** ⚠ Anything the cancelled v3 session allocated after `D-EU-48`
must be reconciled against this range before the next identifier is issued — check
`content/walkthrough_progress_log.csv` and `debugs/docs/` once, then close the question.

---

## 1. What may be quoted, and what may not

🔴 **The S0 quotable perimeter is unchanged and is not reopened by v4**: 149 marker-free certified cells,
`it` = **108.25 kWh/m² ± 0.16 %** heating-only (measured on 35 of the 74), `uk` withheld at fold level,
`es` never quotable, no cell-level number, every `f`-difference carrying both perimeters (92 / 149),
peak-and-timing claims only. The full bar table is v2 §1 — still binding, unedited.

🔴 **No `S2` district EUI may be quoted, and the bar is now higher than v3 stated.** v3 barred them for
`FINDING 208` (no context) and `FINDING 209` (no core). Both of those are largely repaired — every IDF
now carries shading — but three new defects replace them: **`FINDING 211`** (ruled coverage 56.9 %, bar
is 95 %), **`FINDING 212`** (the refusal is a morphology refusal), **`FINDING 213`** (61.1 % of the
simulated IDFs are undivided massing boxes and the viewer disagrees with 459 of them), **`FINDING 214`**
(the EUI denominator never moved to conditioned area). The embargo therefore stands until **`EU-19`**
resimulation lands on plans that have been seen and proven.

⚠ Bologna carries `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on
**100 %** of rows. Never quote a Bologna number without it.

---

## 2. Work packages

| WP | What it is | Status |
|---|---|---|
| `EU-01` … `EU-12` | TABULA loader → results and dossier → district campaign → viewer + pop-up | Completed |
| `EU-13` / `EU-14` / `EU-13B` / `EU-14B` | Layout coverage, Bologna construction year, ruled grid, layout binding | Completed |
| `EU-15` | Ruled thermal zoning to the ≥95 % bar, with the carved unconditioned core | Completed 2026-08-30 — **bar not met, see `FINDING 211`** |
| `EU-16` | 20 m context geometry, adiabatic party walls, four-district resimulation | **Stopped 2026-08-31** (`D-EU-53`) — context/adiabatic landed, resimulation cancelled mid-flight |
| **`EU-17`** | **Relax the box rule — the ruled grid on non-rectangular plates** | **Not started** |
| **`EU-18`** | **Pre-simulation proof: floor-plan atlas, parity gate, non-box sample battery** | **Not started** |
| **`EU-19`** | **Four-district resimulation on proven plans** | **Not started** |

*Status is one of Completed / In progress / Not started. This table carries no notes.*

---

## 3. Open items

All four findings below were measured **2026-08-31** by this session, directly on the artefacts on disk:
the 2,544 side-cars under `outputs_3D/eu_*_data/layouts/` (regenerated 2026-08-31 14:52), the 2,544 IDFs
under `openubem/outputs/eu_evidence/EU-11/<district>/idfs/` (built 2026-08-30 18:xx, plus 2 Madrid stems
rebuilt 2026-08-31 16:23), and the four `prepared_buildings.csv`. Bologna's `D-EU-47` rebuild and Lyon's
`D-EU-48` resubmit never reached this tree — both waves were cancelled by `D-EU-53` — so nothing below
depends on them.

### 🔴 `FINDING 211` — ruled coverage is 56.92 %, and `EU-15` did not move it

`D-EU-39` §1 sets the bar at **≥ 95 % of the buildings of every district**. Measured over all 2,544
side-cars (ruled = `ruled_grid_{1x1,2x1,2x2,3x2,4x2}` ∪ `i_shape_linear_gallery` ∪
`l_shape_decomposition`; refused = `scheme = null`, `geometry_outcome = FALLBACK_PENDING_LAYOUT*`):

| District | side-cars | ruled | refused | ruled % | bar |
|---|---:|---:|---:|---:|---|
| `ES-MAD-BERRUGUETE` | 961 | 616 | 345 | **64.10 %** | FAIL |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 198 | 99 | **66.67 %** | FAIL |
| `GB-LDN-STDUNSTANS` | 82 | 40 | 42 | **48.78 %** | FAIL |
| `IT-BOL-GALVANI2` | 1,204 | 594 | 610 | **49.34 %** | FAIL |
| **fleet** | **2,544** | **1,448** | **1,096** | **56.92 %** | FAIL |

`FINDING 207` measured **57.81 %** (1,469 of 2,541) on 2026-08-30, *before* `EU-15`. `EU-15` T01–T03
("courtyard unfolding, harden the L-shape and gallery routes") therefore delivered **no net coverage**;
what it did deliver is T04 (the strip cutter retired — **0 side-cars carry
`equal_strip_multi_angle_sweep`**, confirmed) and T05 (the core carved — 1,041 side-cars carry
`has_unconditioned_core`, against 0 before). The 843 strip-cutter buildings became refusals, as `D-EU-39`
§2 requires; they were never converted into ruled layouts. **`EU-15` must not be cited as having met its
own acceptance criterion.**

### 🔴 `FINDING 212` — the refusal is a morphology refusal: the box rule

Every refusal carries a `fallback_reason`, and it is attributable (unlike `FINDING 207`, where it was
`None` on all 843). Percentages are of each district's own population:

| Cause | Madrid | Lyon | London | Bologna | fleet |
|---|---:|---:|---:|---:|---:|
| `L_SHAPE_DECOMPOSITION_FAILED` | 220 (22.89 %) | 75 (25.25 %) | 21 (25.61 %) | 313 (25.99 %) | **629 (24.72 %)** |
| `INTERIOR_RING_COURTYARD_UNFOLD_FAILED` | 71 (7.39 %) | 9 (3.03 %) | 0 | 159 (13.21 %) | **239 (9.39 %)** |
| `NARROW_FOOTPRINT_LT_8M` | 4 (0.42 %) | 2 (0.67 %) | 3 (3.66 %) | 135 (11.21 %) | **144 (5.66 %)** |
| `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` | 44 (4.58 %) | 13 (4.38 %) | 18 (21.95 %) | 0 | **75 (2.95 %)** |
| `PARTITION_AUDIT_FAILED` | 6 (0.62 %) | 0 | 0 | 3 (0.25 %) | **9 (0.35 %)** |
| **all refusals** | **345 (35.90 %)** | **99 (33.33 %)** | **42 (51.22 %)** | **610 (50.66 %)** | **1,096 (43.08 %)** |

The gates, with citations, and what each one costs:

1. **The 2 % squaring gate.** `regularize_footprint_orthogonal` fits an orthogonal quadrilateral
   (`european_residential.py:77`, `:101`) and the plate is refused if its area moves more than
   `REGULARIZATION_AREA_DELTA_FALLBACK_FRACTION = 0.02` (`:32`, `:74`, refused at `:918` and `:986`).
   Measured directly: only **2 of 2,544** side-cars exceed 2 % — the gate itself is almost never the
   binding one, because the *morphology dispatch upstream of it* has already sent the non-box plates
   elsewhere.
2. **The reflex-vertex dispatch.** `classify_building_morphology` (`:426`) routes any plate with a
   convex-hull deficit above **3 %** (`:453`) to `l_shape_decomposition`, which splits at the re-entrant
   corner, partitions each wing independently, and **refuses the whole building** if any wing fails
   (`:983`). This is the single biggest cost in the fleet — a quarter of every district. Raw footprint
   complexity is the reason: median raw vertex count before regularization is 9 (Madrid), 9 (Lyon),
   7.5 (London), 11 (Bologna), with a tail to 173 vertices on one Lyon footprint.
3. **The courtyard unfold.** Implemented (`generate_european_courtyard_layout:724`) and failing on
   Bologna's dense perimeter blocks — 13.2 % of that district.
4. **The 8 m narrow-plate gate** (`NARROW_FOOTPRINT_THRESHOLD_M = 8.0`, `:1008`) — 11.2 % of Bologna
   alone; Bologna's stock is deep-and-narrow terraced.
5. **The >8 dwellings/floor cap** (`RULED_GRID_MAX_DWELLINGS_PER_FLOOR = 8`, `:31`, refusal at `:1759`)
   — 22.0 % of London, where the declared per-floor counts reach 35. This one is `FINDING 202`'s
   fail-closed refusal working as designed; it is a **table** limit, not a shape limit, and `D-EU-50`
   does not by itself relax it.

⚪ **Circulation is not box-only in the code.** `CIRCULATION_MIN_DWELLINGS_FOR_CIRCULATION = 2` (`:43`)
and every route carves — grid (`:309`), courtyard (`:739`), gallery (`:783`) — and the L-shape route
carves per wing and combines (`_combine_wing_results:594`). The reason L-shapes look coreless in the
viewer is not the carve, it is (a) refusal, item 2 above, and (b) `keep_circulation_polygon=False` on the
L-shape combine (`:977`), which keeps the area and drops the drawable ring. Measured: **0 floors**
fleet-wide carry circulation area with a null polygon, so (b) currently costs nothing on disk — but it is
the line that will silently un-draw the L-shape cores `EU-17` is about to create.

### 🔴 `FINDING 213` — the viewer and the simulation describe different buildings, on 459 of them

Measured on the IDFs themselves (`_F<i>_whole` zone naming = the one-zone-per-floor massing box;
cross-checked by an independent count of `Zone` objects against declared storeys — both methods return
the identical figures):

| District | IDFs | one zone per floor | with a circulation zone | side-cars declaring a core | **core declared, absent in the IDF** |
|---|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 961 | 520 (54.11 %) | 188 (19.56 %) | 363 | **175** |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 151 (50.84 %) | 57 (19.19 %) | 109 | **52** |
| `GB-LDN-STDUNSTANS` | 82 | 60 (73.17 %) | 13 (15.85 %) | 31 | **18** |
| `IT-BOL-GALVANI2` | 1,204 | 824 (68.44 %) | 324 (26.91 %) | 538 | **214** |
| **fleet** | **2,544** | **1,555 (61.13 %)** | **582 (22.88 %)** | **1,041** | **459 (44.1 % of the cored population)** |

1,555 = the 1,096 refusals of `FINDING 211` **plus 459 buildings the side-car says are ruled**. Of those
459, exactly **2** carry the `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` disclosure; the other
457 are labelled `DWELLING_LAYOUT_EMITTED[_IMPUTED_COUNT]` in both the manifest and the side-car.

Mechanism, with citations: `build_idf_for_building` runs the `FINDING 210` safety net after extrusion —
`find_mismatched_interzone_pairs` / `_has_near_duplicate_vertex_surfaces`, then
`_force_reroute_room_layout_to_one_zone_per_floor` (`scripts/run_eu_s2_campaign.py:516-534`, implemented
at `openubem/idf/surfaces.py:640`), which unions the storey-0 sub-zones back into one block per floor and
**drops the circulation zone with them**. The disclosure that writes the reroute back into
`geometry_outcome` exists (`scripts/run_eu_s2_district_campaign.py:387-390`) but was added **2026-08-31**,
after these IDFs were built on 2026-08-30 — Madrid's two rebuilt stems are the only rows that have it.
The side-car emitter never learns of it at all: it regenerates the layout from the footprint
(`scripts/emit_eu11_layout_sidecars.py`), so a rerouted building keeps advertising the ruled grid.

🔴 **This is the arc's recurring defect, third occurrence.** `FINDING EU-12-01`, then the `D-EU-35`
desync (side-car vs `_geometry`, fixed 2026-08-28 by making the two mirror each other), now the same
divergence re-entering *downstream of both*, inside IDF assembly. A parity check that compares the two
**generators** cannot see it; only a check that reads the **emitted IDF** can. `EU-18`'s parity gate is
specified accordingly.

### 🔴 `FINDING 214` — the EUI denominator never moved to conditioned area

`D-EU-39` §3 ruled that the carve moves every EUI denominator. Measured: `floor_area_m2` equals
`gross_footprint_area_m2` on **2,544 of 2,544** rows and equals `conditioned_floor_area_m2` on **0**
(`scripts/run_eu_s2_district_campaign.py:408-418`, where `floor_area_m2` is assigned the gross sum). Both
areas *are* published beside each other, so the disclosure half of the ruling is met and the arithmetic
half is not. Area conservation itself is exact: conditioned + circulation − gross ≤ 1.2 × 10⁻⁶ relative,
fleet-wide.

Size of the effect on the 582 buildings that carry a core: conditioned/gross means **0.9551** (Madrid),
**0.9598** (Lyon), **0.9083** (London), **0.9359** (Bologna); minima 0.7257 / 0.7121 / 0.6441 /
**0.5189**. Moving the denominator raises those buildings' EUI by ~4–10 % on average and by up to 93 % on
the worst Bologna building. **No published figure may be restated from the current manifest without this
being settled first.**

### ⚪ Resolved by measurement, not a finding

- The v3 director prompt's carried item (ii), *"measured neighbour counts 30.1–49.1 vs the 11.1–12.2 in
  the rules doc"*, **does not reproduce on today's artefacts**: `context_building_count` means are
  **11.88 / 12.28 / 7.52 / 11.22** (Madrid / Lyon / London / Bologna), medians 12 / 12 / 7 / 11, zero
  buildings with an empty context. Three of the four now agree with
  `RULES_context_geometry_simulation_2026-08-30.md` §1 (12.16 / 11.98 / 11.60 / 11.14). **London is the
  single outlier — 7.52 against an expected 11.60 — and is unexplained.** Carry it into `EU-18`.
- Adiabatic coverage re-measured: **89.4 / 86.5 / 70.7 / 80.7 %**, identical to what `EU-16A` T08
  reported, still below the attachment census (99.1 / 97.0 / 92.8 / 88.5 %) and still unexplained on
  disk. Shading coverage is **100 % (2,544 of 2,544)**.

### ⚠ Carried unchanged, not re-measured

`G8.0` FAIL 99/121, `G8.1`–`G8.4` NOT SCOREABLE, `FINDING 181` (closed as declared-and-bounded),
`FINDING 184`, `FINDING 198`, `FINDING 199`, `FINDING 205`, `FINDING 210` (and its `D-EU-43` residual).
`D-EU-37` remains an unruled owner decision. No band was widened.

---

## 4. Rulings taken 2026-08-31

Owner instruction, 2026-08-31, one message; the owner's own words are quoted verbatim under each ruling.

**`D-EU-49` — a single-storey building carries no circulation.**
> *"s'il ya une etage pour une batiment, pas necessaire pour la circulation"*

A stair core exists to connect storeys. A building with one storey gets **no core and no corridor**; its
whole plate is conditioned and its dwellings are partitioned without a carve. Measured scope: **46
single-storey buildings** (Madrid 19, Lyon 6, London 0, Bologna 21 — 1.81 % of the fleet), of which
**3 carry a core today** and lose it: `way/340701289` (Madrid, `ruled_grid_3x2`, 14.519 m²),
`BATIMENT0000000240881213_part0` (Lyon, `ruled_grid_4x2`, 22.3885 m²),
`BATIMENT0000000240881531_part0` (Lyon, `ruled_grid_2x2`, 14.9812 m²). The rule is cheap and correct; it
is **not** a coverage remedy and must never be reported as one.

**`D-EU-50` — the box rule is relaxed; ≥ 95 % per district is proven before simulating.**
> *"je veux relaxer le regle de boite, ce que chose j'ai vue, seulement tu as applique des cirucaiton pour
> des batiments en boite, pourqoui le plan de L ou pas boite. je veux relaxer la regle et tester en avant
> de simualtions. je veux 95%. je veux etre sur en avant des simulations."*

1. A non-rectangular plate — L, U, T, cross, courtyard, narrow — is **expressed**, not refused. The
   ruled grid applies per wing / per unfolded segment; a wing that cannot host its share is re-split or
   re-allocated, never used to refuse the whole building.
2. `D-EU-39` §1's bar is unchanged at **≥ 95 % of the buildings of every district** and is now measured
   **on the emitted IDFs**, not on the side-cars (`FINDING 213` is why).
3. The footprint stays real. Nothing is squared off in the output geometry, no area is invented, and a
   building that genuinely cannot be expressed is refused into the disclosed residual with a named
   reason — the ≤ 5 % residual, not a relabelled success.
4. The `>8 dwellings/floor` cap (`D-EU-39`, `FINDING 202`) is **not** relaxed by this ruling. London's
   22.0 % sits behind it and needs its own decision — flagged, not taken.

**`D-EU-51` — no full campaign without seen plans and a sample battery.**
> *"visualize avec des autres .html pour voir des plan des etages pour chaque quartier pour chaque
> batiment"* … *"en anvant des simulations complet, vas-y tester des simulations des batiment qui n'ont
> pas de plan boite/rectangle"* … *"chaque fois en attendandt des simulations je veux creer une plan en
> avant des simualtions complet avec simulations samples et des visualisations sans que des simulations"*

Standing working method from now on, every campaign, not once:

- **(a) The atlas.** One HTML page per district, every building, showing each storey's plan: dwelling
  polygons, circulation ring, scheme name, storey index, dwelling count, gross and conditioned area.
  🔴 **Drawn from the emitted IDF's zone polygons, never from the side-car** — a viewer that redraws the
  generator's intent cannot detect `FINDING 213`. Separate files from the existing
  `outputs_3D/eu_*_viewer.html`; the 3D viewers are not modified by this.
- **(b) The parity gate.** For every building: the IDF's zone-name set equals the side-car's, the IDF's
  circulation-zone presence equals `has_unconditioned_core`, and any reroute is written back into
  `geometry_outcome`. The gate **fails closed** — a divergence stops the campaign; it is never reported
  as a coverage percentage.
- **(c) The sample battery.** Real EnergyPlus 23.1.0 locally (`C:\EnergyPlusV23-1-0\energyplus.exe`),
  on **non-box buildings only**, before any `sbatch`: at least six buildings per refusal class per
  district where that class exists (L-shape, courtyard, narrow, >8/floor, audit-failed) plus six former
  reroute casualties. Report RC, severe and fatal counts per building. 🔴 A Python-only geometric check
  is **not** proof — this arc has already had one false-green on exactly that shortcut
  (`T09-FINDING210-ROOTCAUSE-FIX-V2`).
- **(d) The order.** Atlas and battery are read and accepted by the owner **before** the Speed
  submission is even prepared. Preparing SLURM files does not authorise submitting them.

**`D-EU-52` — the arc keeps its own error index.**
> *"nous avons progresse breacoup et ont confronte plus des erruers creer une document des erreurs comme
> ça … specifique pour la projet de … europeanLocations"*

`debugs/DEBUG_REFERENCES_european_locations.md`, modelled on
`C:\Users\o_iseri\Desktop\idf_reader\docs_BEM_Explanation\debug_References.md`. Searched **before** any
debugging in this arc, appended **after** any fix, house format
(`- **<exact symptom>** — <cause>. Fix: <what changed, file:line>. *(source doc)*`). It does not replace
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` — that file stays the repo-wide index and the
CLAUDE.md hard rule still applies; the arc file is the arc-scoped view and routes to it.

**`D-EU-53` — the Speed runs and the v3 track are cancelled; only v4 proceeds.**
> *"j'annule des runs sur le speed et annuler des taches v3, desormais, nous allons concentrer seuelemnt
> v4, tu continues ce que chose tu fait vas-y"*

1. The `D-EU-47` Bologna rebuild wave (job `1303039`, 176 tasks) and the `D-EU-48` Lyon timeout resubmit
   (job `1303023`, 9 tasks) are cancelled and will not be harvested. `EU-16`'s resimulation half is
   stopped where it stands.
2. v3's `STATE`/`BRIEF` and every prompt written against them are historical. No further dispatch is made
   from `prompts/PROMPT_D-EU-47_*`, `prompts/PROMPT_D-EU-48_*` or `prompts/PROMPT_EU-VAL_*` — the T10
   audit is re-scoped into `EU-18`, which audits the plans, not the cancelled campaign.
3. 🔴 **Nothing is dropped by the cancellation.** Bologna's **177 `FAILED`** (85 `FINDING 210` + 52
   `D-EU-43` + 40 zero-area) and Lyon's **9 `TIMEOUT`** stay recorded as failures with a named class,
   are never pooled around, and are recovered inside `EU-19`'s resimulation on the new plans. The single stem
   excluded pre-ship under `D-EU-47` (`635c1d7d41a92830` / building 31741, unresolved reroute) stays
   disclosed, not fixed.
4. Before `EU-19` is prepared, confirm this arc has **no job left in the Speed queue** — a
   report-only `squeue -u o_iseri` / `sacct` check, delegated, never a login-node computation.

⚡ **Compute rule, unchanged and reinforced.** Speed only, `sbatch --array` fire-and-forget, never the
login node; EnergyPlus 23.1.0 Ubuntu20 under `/speed-scratch/o_iseri/openubem/tools/`; waves under the
~20k task cap. **`--time=7-00:00:00` minimum on every submission** — the cancelled v3 wave recorded a
Lyon resubmit timing out twice at 3 h. A Speed number and a Windows number are not the same measurement
(`FINDING 187`, `FINDING 190`).

---

## 5. Acceptance — what `EU-17` and `EU-18` must show

`EU-17` is done when, measured on the **emitted IDFs** and not on side-cars:

1. Ruled coverage ≥ **95 %** in each of the four districts, with the residual listed by named reason.
2. **0** buildings where the side-car declares a layout the IDF does not carry (`FINDING 213` → 0).
3. Every multi-storey ruled building with ≥ 2 dwellings/floor carries its circulation zone in the IDF;
   every single-storey building carries none (`D-EU-49`).
4. Dwelling conservation holds — no count reduced anywhere, 28,189 the floor, not the ceiling.
5. Area conservation holds per building (conditioned + circulation = gross, ≤ 1 × 10⁻⁶ relative), and
   the EUI denominator question of `FINDING 214` is settled explicitly, in writing, either way.

`EU-18` is done when the atlas exists for all four districts, the parity gate returns zero divergences,
and the sample battery returns RC 0 with zero fatals on every sampled non-box building — reported per
building, never pooled.

---

## 6. Where things are

| What | Where |
|---|---|
| Plain-language brief | `BRIEF_european_locations_v4.md` |
| Arc error index (`D-EU-52`) | `debugs/DEBUG_REFERENCES_european_locations.md` |
| Repo-wide error index | `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` |
| Dwelling-layout rule + acceptance test | `rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md`, `rules/RULES_dwelling_layout_scheme_2026-08-28.html` |
| Context-geometry rule | `rules/RULES_context_geometry_simulation_2026-08-30.md` |
| Layout code under change | `openubem/geometry/european_residential.py` (routes `:426`, `:724`, `:767`, `:855`; gates `:32`, `:1008`, `:31`) |
| IDF build + reroute | `scripts/run_eu_s2_campaign.py:516-534`, `openubem/idf/surfaces.py:640` |
| District campaign + manifests | `scripts/run_eu_s2_district_campaign.py` (`_geometry:112`, areas `:408-418`) |
| Side-car emitter (viewer layer) | `scripts/emit_eu11_layout_sidecars.py` |
| Emitted IDFs + `prepared_buildings.csv` | `openubem/outputs/eu_evidence/EU-11/<district>/` |
| Side-cars / viewers (mirror) | `outputs_3D/eu_*_data/layouts/`, `outputs_3D/eu_*_viewer.html` |
| Superseded v3 (historical, not executed) | `STATE_european_locations_v3.md`, `BRIEF_european_locations_v3.md`, `prompts/DIRECTOR_PROMPT_european_locations.md` (still points at v3 — repoint) |
| Append-only progress log | `content/walkthrough_progress_log.csv` |

**Suite baseline:** `pytest -q -n 8 tests/` → **2,345 passed / 55 skipped** in ~7 min. Cite the enumerated
55-skip list, never the bare count. ⚠ Two pre-existing failures in
`tests/test_eu_real_footprint_feasibility.py` are known and untouched (`EU-13B` §10).

---

## 7. What happens next

1. Write `implementation/PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` — `EU-17` then `EU-18`, tasks with
   What / Why / How / How to test, stop-and-report after the coverage census and after the atlas.
2. Dispatch `EU-17` to a fresh Sonnet session. Nothing reaches Speed until `EU-18` (c) is read.
3. Housekeeping, one pass, not urgent: repoint `prompts/DIRECTOR_PROMPT_european_locations.md` at v4,
   move the three cancelled `PROMPT_*` files and the v3 `STATE`/`BRIEF` to `previous/` with the citation
   sweep the archiving rule requires, reconcile the identifier ledger (§0), and confirm the Speed queue
   is empty (`D-EU-53` item 4).
