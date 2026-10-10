# European locations × Step 8 — arc state (v3)

**Opened:** 2026-08-30. **Supersedes** `previous/STATE_european_locations_v2.md` (frozen, not appended to).
History — every ruling, finding, gate table and acceptance record — stays in
`previous/MVP_european_locations.md`, `previous/WALKTHROUGH_european_locations.md` and the frozen v2.

**This document carries current truth only.** Replace an entry when it stops being current; never append
below it.

- Plain-language brief (goal → problems → fix → plan): [`BRIEF_european_locations_v3.md`](BRIEF_european_locations_v3.md)
- Plan in force: [`implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md`](implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md)
- Rules an executor is validated against: [`rules/`](rules/) — dwelling layout, and context geometry.

---

## 1. What may be quoted, and what may not

🔴 **The S0 quotable perimeter is unchanged and is not reopened by v3**: 149 marker-free certified cells,
`it` = **108.25 kWh/m² ± 0.16 %** heating-only (measured on 35 of the 74), `uk` withheld at fold level,
`es` never quotable, no cell-level number, every `f`-difference carrying both perimeters (92 / 149),
peak-and-timing claims only. The full bar table is v2 §1 — it is still binding, unedited.

🔴 **No `S2` district EUI may be quoted at all until `EU-16` resimulation lands.** The four current pooled
figures were produced on **free-standing buildings in an empty field** — `FINDING 208` — and without the
ruled unconditioned core — `FINDING 209`. They are recorded here as the state of the model, not as results:

| District | pooled heating EUI | Speed job | population run / success |
|---|---:|---|---|
| `ES-MAD-BERRUGUETE` | 81.5325 kWh/m² | `1297338` | 952 / 914 |
| `FR-LYO-HAUTCOEURPENTES` | 69.5235 kWh/m² | `1297355` | 283 / 277 |
| `GB-LDN-STDUNSTANS` | 86.8703 kWh/m² | `1297373` | 80 / 76 |
| `IT-BOL-GALVANI2` | 47.4921 kWh/m² | `1298672` | 1,201 / 1,184 |

⚠ Bologna carries `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on
**100 %** of rows. Never quote a Bologna number without it.

---

## 2. Work packages

| WP | What it is | Status |
|---|---|---|
| `EU-01` … `EU-12` | TABULA loader → results and dossier → district campaign → viewer + pop-up | Completed |
| `EU-13` | Dwelling-layout coverage extension | Completed |
| `EU-14` | Bologna construction year (ISTAT imputation) | Completed |
| `EU-13B` | Ruled grid, per-storey conservation, `>8`/floor cap, resimulation | Completed 2026-08-30 |
| `EU-14B` | Bologna layout binding + resimulation | Completed 2026-08-30 |
| **`EU-15`** | **Ruled thermal zoning to the ≥95 % bar, with the carved unconditioned core** | **Completed 2026-08-30** |
| **`EU-16`** | **20 m context geometry, adiabatic party walls, four-district resimulation** | **In progress** |

*Status is one of Completed / In progress / Not started. This table carries no notes. Maintained from
`content/walkthrough_progress_log.csv`.*

⚠ **Namespace warning.** `EU-NN` here is a **work package**. The 2026-08-26 files
`debugs/docs/DONE-docs/DECISION_REQUEST_EU-15_gate5_winter_exceptions_*` and
`..._EU-16_diary_year_*` are *decision requests* from the pre-`D-EU-NN` naming and are unrelated to the
work packages `EU-15` / `EU-16` above. Decisions are `D-EU-NN` from `D-EU-19` onward.

✅ **`FINDING 201` is CLOSED.** Dwelling conservation re-measured 2026-08-30 over all 2,312 emitted
side-cars, on distinct zone names: **28,189 declared → 28,189 zones, 0.00 %, 0 non-conserving.** The
`ceil(total ÷ storeys)` defect is gone. `FINDING 202` (`>8`/floor) is closed by the fail-closed refusal —
75 buildings refused, none reduced.

---

## 3. Open items — the two defects `EU-15` and `EU-16` exist to fix

🔴 **`FINDING 207` — ruled-scheme conformance is 57.81 % of the fleet, not the 93.6 % / 88.1 % the results
documents report.** `geometry_outcome = DWELLING_LAYOUT_EMITTED*` counts the **non-ruled** secondary
`equal_strip_multi_angle_sweep` strip cutter as a success, so the published coverage figures hide it.
Measured 2026-08-30 over all 2,541 side-cars in `outputs_3D/`:

| District | side-cars | ruled scheme | secondary strip | no layout | ruled % |
|---|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 961 | 627 | 284 | 50 | 65.2 % |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 201 | 81 | 15 | 67.7 % |
| `GB-LDN-STDUNSTANS` | 82 | 45 | 16 | 21 | 54.9 % |
| `IT-BOL-GALVANI2` | 1,201 | 596 | 462 | 143 | 49.6 % |
| **fleet** | **2,541** | **1,469** | **843 (33.2 %)** | **229 (9.0 %)** | **57.81 %** |

Ruled scheme = `ruled_grid_{1x1,2x1,2x2,3x2,4x2}` ∪ `i_shape_linear_gallery` ∪ `l_shape_decomposition`.
At storey level, **3,763 of 10,650 partitions (35.3 %)** are on the strip cutter. Two named causes, both
disclosed by the executor: **`courtyard_secondary` (MVP §6.4 three-wing unfolding) is not implemented**, and
the reflex-vertex / gallery dispatch falls back rather than mislabel a noisy GIS footprint. ⚠ **`fallback_reason`
is `None` on all 843**, so the split between the two is not attributable from disk today.
**`D-EU-39` sets the bar at ≥ 95 % per district, so 57.81 % fails it in every district.**

🔴 **`FINDING 208` — every European building was simulated alone in an empty field.** Measured 2026-08-30:
**0 of 2,516** EU-11 district IDFs carry a `Shading:*` object, and **0 of 2,516** carry an `Adiabatic`
surface. Cause is one line — `scripts/run_eu_s2_campaign.py:227` calls
`extrude_geometry(idf, zones, [])`, hard-coding an empty context list, and `set_adiabatic_surfaces`
(`openubem/idf/surfaces.py:909`) is never called on this path. `Solar Distribution` is `FullExterior` and
there is no `ShadowCalculation` object. Exposure, measured over `01_buildings_clean.gpkg`:

| District | all buildings | neighbours within 20 m (mean / max) | attached to ≥1 neighbour |
|---|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 2,381 | 12.16 / 26 | 99.1 % |
| `FR-LYO-HAUTCOEURPENTES` | 1,455 | 11.98 / 28 | 97.0 % |
| `GB-LDN-STDUNSTANS` | 2,406 | 11.60 / 25 | 92.8 % |
| `IT-BOL-GALVANI2` | 1,631 | 11.14 / 28 | 88.5 % |

Every simulated building is missing ~11–12 shading neighbours, and 88.5–99.1 % of them lose heat through
walls they physically share with a neighbour. **This invalidates all four district EUIs for quotation.**

🔴 **`FINDING 209` — no building in the fleet has the ruled unconditioned core.**
`has_unconditioned_core = false` on **2,541 of 2,541**, and `circulation_area_m2_total > 0` on only **324**
(the `2×2`, `3×2`, `4×2` and gallery routes). Circulation is computed and drawn but never **carved**, because
`D-EU-36`'s carve-versus-add half was unruled and `EU-13B` `T06` stayed blocked. Two further gaps against
the rule, which gives a stair core to **2–4** dwellings per storey: **682 `ruled_grid_2x1`** and
**62 `l_shape_decomposition`** buildings carry no circulation at all. The core is the mechanism behind the
party-wall buffering the MVP cites ($b_u = 0.50$–$0.80$, 30–50 % transmission moderation); without it the
model is not the ruled model.

⚠ **Carried unchanged from v2, not re-measured:** `G8.0` FAIL 99/121 carried, `G8.1`–`G8.4` NOT SCOREABLE,
`FINDING 181` closed as declared-and-bounded, `FINDING 184` (annual claims unsupported), `FINDING 198`
(Lyon composition vs EUI, deepened at 94.7 % partitioned), `FINDING 199` (Bologna 47.4921 further inside
DR16 INCOMPATIBLE, not corrected), `FINDING 205` (London 86.8703 crosses DR15's CONSISTENT ceiling into
WORTH INVESTIGATING). `D-EU-37` (typology-table extension) is still an unruled owner decision, and no band
was widened.

---

## 4. Rulings taken 2026-08-30

**`D-EU-39` — the ruled MVP §4.2–§4.4 scheme is mandatory, and circulation is CARVED.** Owner instruction,
2026-08-30. Three parts:
1. Every conditioned floor is divided into residential thermal zones by the ruled grid
   (`1×1`, `2×1`, `2×2`, `3×2`, `4×2`), on **≥ 95 % of the buildings of every district** — a fleet average is
   no longer sufficient, London and Bologna included.
2. `equal_strip_multi_angle_sweep` is **retired as a success path**. A building the ruled route cannot express
   is refused into the disclosed residual; it is never relabelled as emitted.
3. **Carve-versus-add is resolved as CARVE** — the open half of `D-EU-36`. The unconditioned stair core
   (§4.3, 6–12 % of plate, centroidal, extruded z=0→roof) and the 1.80 m double-loaded corridor spine
   (`L/W ≥ 2.0`) are cut out of the observed plate. The footprint stays real; conditioned area falls.
   **Conditioned area must be published beside gross footprint area for every building**, and every EUI
   denominator moves. `EU-13B` `T06` is unblocked by this.
   ⚪ Adding area outside an observed footprint was refused: a denominator change is disclosable, a false
   footprint is not.

**`D-EU-40` — every building is simulated with its 20 m context, and attached walls are adiabatic.** Owner
instruction, 2026-08-30, restoring the published method of record (Koral Iseri et al., *Energy & Buildings*
337 (2025) 115620, §4.1.1 and Fig. 4b): each residential building is simulated **individually and
sequentially**, with **all** buildings whose footprint lies within **20 m** — residential and
non-residential alike — emitted as non-simulated shading geometry, and with intersecting walls between
attached buildings treated as **adiabatic** surfaces. Full rule, including the 20 m-versus-30 m conflict with
`config.SHADING_SPHERE_RADIUS`: [`rules/RULES_context_geometry_simulation_2026-08-30.md`](rules/RULES_context_geometry_simulation_2026-08-30.md).

**`D-EU-41` — `R6`'s named implementation is wrong; the physical rule stands.** Manager ruling, 2026-08-30,
raised by the `EU-16A` executor, which stopped correctly on the conflict rather than resolving it.
`set_adiabatic_surfaces` (`openubem/idf/surfaces.py:909`) is a documented **no-op stub** and its signature
`(idf, zones, strategy)` carries no neighbour footprints, so it can never implement an inter-building flip —
both `D-EU-40` `R6` and `T07` asserted otherwise and are corrected. `openubem/idf/surfaces.py` stays
**non-editable**; the party-wall flip is a European-only pass in `scripts/run_eu_s2_campaign.py` reusing
`build_european_context`'s own neighbour rows and transform. `R9` gains one disclosure: **flipped exterior
wall area as a fraction of total exterior wall area**, because an IDF count alone cannot distinguish one wall
from half an envelope. Full amendment: [`rules/RULES_context_geometry_simulation_2026-08-30.md`](rules/RULES_context_geometry_simulation_2026-08-30.md) §2 `R6`.

⚪ **Next free identifier `D-EU-42`, next free finding `FINDING 210`.**
⚪ `FINDING 206` is spent — the viewer's circulation ring was computed but never drawn; fixed 2026-08-30
(`debugs/docs/INVESTIGATION_viewer-circulation-not-drawn_2026-08-30.md`).

⚡ **Compute rule, unchanged.** Speed only, `sbatch --array` fire-and-forget, never the login node;
EnergyPlus 23.1.0 Ubuntu20 under `/speed-scratch/o_iseri/openubem/tools/`, pattern
`scripts/cluster/submit_fleet_t08.sbatch`, waves under the ~20k task cap. A Speed number and a Windows
number are not the same measurement (`FINDING 187`, `FINDING 190`).

⚡ **Walltime, new 2026-08-31.** Every submission requests `--time=7-00:00:00` minimum (partition `ps`
max; SLURM bills actual usage, not requested time) — never a short hours-based guess, overridden on the
CLI, never baked into the shared `.sbatch` script. Cause: D-EU-48's Lyon resubmit at `--time=03:00:00`
timed out a second time on 6/9 stems. See `CLAUDE.md` §CLUSTER.

---

## 5. Where things are

| What | Where |
|---|---|
| Plain-language brief | `BRIEF_european_locations_v3.md` |
| Plan in force | `implementation/PLAN_eu15-eu16-zoning-context-2026-08-30.md` |
| Dwelling-layout rule + acceptance test | `rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md`, `rules/RULES_dwelling_layout_scheme_2026-08-28.html` |
| Context-geometry rule | `rules/RULES_context_geometry_simulation_2026-08-30.md` |
| Method of record — floor layouts | `MVP` §4.2–§4.4 + `content/figure_4_2_dwelling_layout_schemes.svg`; `GSSCanada/.../IMP_step8/outputs/floor_layout_generation_report.md` §3, §5–§9 |
| Method of record — context + zoning | `GSSCanada/.../IMP_step8/resources/1-s2.0-S0378778825003500-main.pdf` p. 9 (Fig. 4) |
| Grasshopper → Python reference | `GSSCanada/.../IMP_step8/extracted_scripts/` (`008_HB_EPContextSrf_idx1574.py` = context surfaces) |
| Frozen history | `previous/STATE_european_locations_v2.md`, `previous/MVP_european_locations.md`, `previous/WALKTHROUGH_european_locations.md` |
| Append-only progress log | `content/walkthrough_progress_log.csv` |
| Ruled / open decision requests | `debugs/docs/DONE-docs/` (ruled), `debugs/docs/` (open) |
| Result write-ups | `results/RESULTS_EU-11.md`, `openubem/outputs/eu_evidence/EU-13B/RESULTS_EU-13B.md`, `.../EU-14B/RESULTS_EU-14B.md` |
| Viewers (mirror of `openubem/outputs/3D/`) | `outputs_3D/eu_*_viewer.html` + `eu_*_data/` |
| Director prompt | `prompts/DIRECTOR_PROMPT_european_locations.md` |

**Suite baseline:** `pytest -q -n 8 tests/` → **2,345 passed / 55 skipped** in ~7 min. Cite the enumerated
55-skip list, never the bare count. ⚠ Two pre-existing failures in
`tests/test_eu_real_footprint_feasibility.py` are known and untouched (`EU-13B` §10).
