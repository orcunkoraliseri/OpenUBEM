# STATE — EU-21 executors, stopped mid-flight

- **Date stopped:** 2026-09-01
- **Reason:** owner instruction ("just stop everything please"). Not a failure, not a rollback.
- **Working tree:** untouched after the kill. Nothing reverted, nothing committed.
- **Governing plan:** `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu21-group-schemes-2026-09-01.md`
- **Standing block:** `D-EU-55` — no EnergyPlus run of any kind without the owner's own sentence. Writing `.idf` is allowed; running one is not.

---

## Agent A — "EU-21 P01b+P01c sidecar and ladder"

### Code that landed (on disk, working)

| File | What |
|---|---|
| `scripts/emit_eu11_layout_sidecars.py` | P01b — the side-car now keeps the ruled rings when the IDF reroutes, and flags them `idf_reroute_divergence: true` instead of blanking `floors` / `scheme` / `scheme_by_storey`. 13 references to the flag. |
| `openubem/idf/surfaces.py` | P01c — the intersect ladder. `_snap_shared_interzone_vertices` at `:774` (P01's no-op, kept), the ladder comment at `:823`, and rung (2) `idf.match()` alone at `:943`. |

### Rebuild state — `openubem/outputs/eu_evidence/EU-21/`

| District | IDFs written | Side-cars emitted | Expected |
|---|---|---|---|
| ES-MAD-BERRUGUETE | 961 | 0 | 961 |
| FR-LYO-HAUTCOEURPENTES | 297 | **297** | 297 |
| GB-LDN-STDUNSTANS | 82 | 0 | 82 |
| IT-BOL-GALVANI2 | **496** (killed mid-run) | 0 | 1,204 |

Killed while rebuilding Bologna, last reported progress 345/1204; 496 IDFs on disk at kill time.

### Measured before the kill — Lyon only, and it is the load-bearing number

- **196 / 297 = 66.0 %** of Lyon side-cars now carry a drawable floor plan (`len(floors) > 0`).
- Prior state on the EU-17 IDFs was **35.4 %** for Lyon, **21.3 %** (541/2,544) fleet-wide.
- Outcome split: 112 `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` · 84 `..._INTERZONE_MISMATCH_REROUTED` · 101 `FALLBACK_PENDING_LAYOUT`.
- **84** side-cars carry `idf_reroute_divergence: true` — drawable, and never quotable as energy.
- Schemes seen: `ruled_grid_1x1` 88 · `ruled_grid_2x1` 55 · `ruled_grid_3x2` 31 · `ruled_grid_2x2` 18 · `ruled_grid_4x2` 1 · `i_shape_linear_gallery` 1 · `narrow_plate_corridor_free` 1 · `l_shape_decomposition` 1.

### Not done

1. Rebuild + side-car emission for Madrid, London, Bologna.
2. Fleet REROUTED tally after the ladder (target was < 100; unmeasured).
3. The honesty measure — count of geometrically-interior walls left `Outdoors` by `match()` alone.
4. Full `pytest -q -n 8 tests/` against the 2,551 passed / 55 skipped / 6 pre-existing-failure baseline.
5. Debug-reference bullet in `debugs/DEBUG_REFERENCES_european_locations.md`.
6. Two §8 progress-log entries in the plan doc.

### To resume

`python -m scripts.run_eu_s2_district_campaign --district <D> --out openubem/outputs/eu_evidence/EU-21/<D>` for ES, GB, IT — Bologna needs its 496 partial IDFs regenerated or resumed — then re-emit side-cars for all four.

---

## Agent B — "EU-21 P02-P05 four layout schemes"

### Code that landed (on disk, working)

All four generators exist in `openubem/geometry/european_residential.py`:

| Task | Function | Line |
|---|---|---|
| P02 / S1 | `generate_european_courtyard_perimeter_band_layout` | `:1465` |
| P03 / S2 | `generate_european_row_house_depth_bands_layout` | `:1544` |
| P04 / S3 | `generate_european_wing_spine_decomposition_layout` | `:1595` |
| P05 / S4 | `generate_european_regularized_envelope_grid_layout` | `:1723` |

15 references to the four scheme strings in that file.

### State at kill

Killed at **88 %** of its full pytest run. The test verdict was never returned, so the four schemes are **written but unverified** — no regression baseline comparison exists for them.

### Not done

1. Full pytest verdict vs the 2,551 / 55 / 6 baseline.
2. Measurement harness over the four districts — how many of the 1,062 refusals each scheme recovers.
3. Per-task refusal breakdown.
4. Debug-reference bullet.
5. Four §8 progress-log entries.

### To resume

Run the suite first. Until it is green, treat the four generators as unproven code sitting in a load-bearing file.

---

## Where the 95 % bar stands

- Fleet 2,544 residential buildings across four districts; 95 % = **2,417**.
- Measured on the EU-17 IDFs: **541 = 21.3 %**.
- Lyon after P01b: 66.0 %. If P01b behaves the same everywhere, the fleet lands at roughly **1,482 = 58 %** — recovery of already-computed plans, no new shapes.
- The remaining ~935 buildings are refusals of *shape*. They are what P02–P05's four schemes exist to answer, and that gap is unmeasured.
- Per-group split of the gap: see `rules/RULES_dwelling_layout_groups_2026-09-01.html`.
