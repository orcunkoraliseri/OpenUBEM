# MEASUREMENT — OPEN-10: the "90 buildings" figure, settled fleet-wide

> **Task:** C03, `PLAN_compute-queue.md` §5. **Type:** classification + band arithmetic only —
> **no EnergyPlus invoked, no IDF simulation run, no `.idf` file written to disk.** Uses the
> project's own `layout_assigner.compute_band_map()` / `layout_assigner.match_storeys()` —
> neither reimplemented. **HEAD read at:** `9270ac7d06e0897e4b2b65dc0c72a0f6d246accb` (2026-08-06).
> **Predecessor:** `MEASUREMENT_open-10_zonegroup-capability.md` (N11) — this task re-derives, at
> full fleet scale, the number N11 said was "documented with a path:line, but not currently
> re-derivable within [N11's] no-compute constraint."

## Verdict

**Yes — the carried "90 buildings" figure reproduces exactly, per archetype, with no adjustment:
66 `MidriseApartment` + 24 `HighriseApartment` = 90.** Every one of those 90 is `fallback_not_expressible`
under the shipped `Zone.Multiplier` mechanism today, and every one of the 90 becomes expressible
(`applied` or `identity`) under N11's proposed direct-`ZoneGroup`-overwrite mechanism — a 100% flip
rate, matching N11's claim precisely. **Population, code, and definition are all unchanged** from
the source crosstab; this is a clean reproduction, not a re-derivation that needed reconciling.

---

## 1. Method

1. Loaded `05_results.gpkg` for all **twelve** cells (the only per-building fleet artifact that
   carries `archetype_id`/`levels`/`height_m` for the **full** population, including the 6
   buildings that never simulated — see §5, "provenance note," for why this file and not
   `01_buildings.gpkg`).
2. Derived `num_floors` per building using the project's own
   `openubem.geometry.footprint.derive_num_floors()` (unchanged, not reimplemented).
3. Joined `archetype_id` against `layout_assigner.ARCHETYPE_IDF_MAP` to isolate the population this
   item is about.
4. For each mapped building, loaded that archetype's baseline IDF once (cached by resolved file
   path — 16 distinct files for the 16 archetype IDs actually present in the fleet), called
   `layout_assigner.compute_band_map(idf)` once per file, and called
   `layout_assigner.match_storeys(idf, num_floors, band_map)` once per building — the same function,
   same call signature, same code path `openubem/idf/builder.py:451-452` uses in production.
5. For the two archetypes that carry a real `ZoneGroup` (`MidriseApartment`, `HighriseApartment`),
   additionally called `match_storeys()` a second time per building with a **counterfactual**
   `band_map` — a copy with the target (middle) band's `storeys_in_band` forced to `1` instead of
   its baked-in `2`/`8`. This models N11's proposed mechanism (writing the `ZoneGroup`'s own `Zone
   List Multiplier` field directly, rather than compounding a residual `Zone.Multiplier` on top of
   it) using the **real, unmodified `match_storeys()` residual-solving code** — only the one input
   field N11 identified as the mechanism difference (the baked-in list multiplier `match_storeys()`
   reads from `band_map`) was changed. No band-matching or residual logic was rewritten.

No sampling, no truncation, no top-N cap: **all 8,160 fleet buildings were read; all 7,442 with an
`ARCHETYPE_IDF_MAP` entry were classified.** Single-threaded, no multiprocessing — the whole pass
(16 IDF parses + 7,442 pure-Python `match_storeys()` calls, plus 90 counterfactual calls) completes
in a few seconds; no contention with any concurrently running simulation.

---

## 2. Population check against the register

| Quantity | Register (carried) | This measurement |
|---|---|---|
| Fleet total | 8,160 | 8,160 |
| No `ARCHETYPE_IDF_MAP` entry | 718 | **718** (650 `OpenUBEMUnknown` + 68 `Courthouse`) |
| Evaluated (mapped) | 7,442 | **7,442** |

Population is an **exact match**. No compute-side sampling or exclusion was applied.

---

## 3. Fleet-wide status under the shipped mechanism, all mapped archetypes

| `status_shipped` | count |
|---|---:|
| `fallback_shorter` | 3,724 |
| `fallback_not_expressible` | **1,976** |
| `identity` | 1,226 |
| `applied` | 516 |
| **Total** | **7,442** |

`fallback_not_expressible`, by archetype (10 archetypes hit this status; sums to 1,976 exactly):

| archetype_id | n fallback_not_expressible | n in fleet (this archetype) | `n_proto` (baseline band count) | has `ZoneGroup`? |
|---|---:|---:|---:|---|
| `SmallOffice` | 1,580 | 3,504 | 2 (no middle band) | no |
| `LargeOffice` | 175 | 270 | 4 (≥2 middle bands) | no |
| `TallBuilding` | 88 | 92 | 20 (≥2 middle bands) | no |
| `MidriseApartment` | **66** | 2,818 | 3 (1 middle band, list mult 2) | **yes** |
| `SuperTallBuilding` | 24 | 24 | 30 (≥2 middle bands) | no |
| `HighriseApartment` | **24** | 32 | 3 (1 middle band, list mult 8) | **yes** |
| `QuickServiceRestaurant` | 7 | 50 | 2 (no middle band) | no |
| `SecondarySchool` | 7 | 11 | 2 (no middle band) | no |
| `FullServiceRestaurant` | 4 | 33 | 2 (no middle band) | no |
| `Hospital` | 1 | 5 | 6 (≥2 middle bands) | no |

**66 + 24 = 90.** This is the register's exact figure, reproduced by running the current shipped
code against every real fleet building's real `(archetype_id, num_floors)` pair — not adjusted to
land there.

---

## 4. The `ZoneGroup` gain, applied to exactly the 90

| archetype | shipped `fallback_not_expressible` | proposed-mechanism outcome | flip rate |
|---|---:|---|---:|
| `MidriseApartment` | 66 | all 66 → `applied` | **66/66 = 100%** |
| `HighriseApartment` | 24 | all 24 → `applied` | **24/24 = 100%** |

Full shipped-vs-proposed breakdown (all 2,818 `MidriseApartment` / 32 `HighriseApartment` buildings,
not just the flipped ones):

| archetype | shipped | proposed |
|---|---|---|
| `MidriseApartment` (n=2,818) | `fallback_shorter` 2,273 · `identity` 343 · `applied` 136 · `fallback_not_expressible` 66 | `fallback_shorter` 2,273 · `identity` 343 · `applied` 202 |
| `HighriseApartment` (n=32) | `fallback_not_expressible` 24 · `applied` 5 · `fallback_shorter` 3 | `applied` 29 · `fallback_shorter` 3 |

`applied + identity` (i.e. "expressible") rises from 479→545 for `MidriseApartment` (+66) and from
5→29 for `HighriseApartment` (+24) — both deltas equal the flip count exactly, and no other status
bucket moved.

**The two limits N11 established hold under this fleet-wide run, not just by assertion:**

1. **`n_real ∈ {1,2}` stays inexpressible under either mechanism.** `fallback_shorter` counts are
   **identical** between shipped and proposed for both archetypes (2,273 and 3) — the counterfactual
   band map does not touch this branch (`match_storeys()` returns `fallback_shorter` before the
   multiplier logic runs at all).
2. **The gain applies only to the two `ZoneGroup`-carrying archetypes.** The counterfactual was
   computed only for `MidriseApartment`/`HighriseApartment`; the other 1,886 (1,976 − 90)
   `fallback_not_expressible` buildings belong to 8 archetypes with **structural** middle-band
   ambiguity (`n_proto == 2`, no middle band at all, or `n_proto ≥ 4` with multiple middle bands —
   `layout_assigner.py:557-563`), which a `ZoneGroup` field edit does not touch: there is no
   ambiguity about *which value* to write, there is ambiguity about *which band* to write it to.

---

## 5. A clarification the fleet-wide run surfaces, not a contradiction

N11's write-up named 7 archetypes as the "structural" `fallback_not_expressible` population:
`Hospital, LargeOffice, TallBuilding, SuperTallBuilding, College, LargeHotel, Laboratory`. That list
was **illustrative from A1's 25-file library cross-tab, not a fleet-population claim**, and the
shipped code's own branch condition it cites (`n_proto == 2` with no middle band, **or** `n_proto ≥ 4`
with more than one middle band) already covers more than those 7 names. Checked directly against
the real fleet:

- **3 of N11's 7 named archetypes have zero fleet representation**: `College`, `LargeHotel`,
  `Laboratory` — 0 buildings each in all twelve cells. Their structural ambiguity is real (verified
  by `compute_band_map()` directly: `n_proto` 4, 4, 6 respectively, all multi-band), it simply never
  gets exercised by any real building.
- **4 archetypes not named by N11 also carry the same `n_proto == 2` structural condition and do
  appear in the fleet, in large numbers**: `SmallOffice` (`n_proto=2`, **1,580** fallback buildings —
  the single largest bucket in the whole table, 16× the apartment total), `QuickServiceRestaurant` (7),
  `SecondarySchool` (7), `FullServiceRestaurant` (4).

Practical consequence: the two `ZoneGroup` archetypes' 90 buildings are **4.6%** of the 1,976
fleet-wide `fallback_not_expressible` population; fixing only the `ZoneGroup` mechanism (as N11
scoped it) would leave **95.4% (1,886 buildings)** — dominated by `SmallOffice` alone — exactly as
not-expressible as before. This is consistent with N11's own stated scope limit (§4 above), just
quantified at fleet scale for the first time.

---

## 6. Provenance note — why `05_results.gpkg`, not `01_buildings.gpkg`

`01_buildings.gpkg` (`docs/docs_VALIDATION/validations/overAll/results/phaseE/<cell>/01_buildings.gpkg`)
is the true Stage-1 (data acquisition) artifact — it has **no `archetype_id` column at all** (verified
by direct column read, all twelve cells share the same 23-column schema). No standalone Stage-2
(semantic enrichment) file is persisted anywhere in the `phaseE` results tree — only Stage-1
(`01_buildings.gpkg`), the Stage-3/4 simulation manifest (`04_simulation_manifest.parquet`, no
`archetype_id` either), and Stage-5 (`05_results.gpkg`). `archetype_id`/`levels`/`height_m` are Stage-2
assignments that pass through Stage 3/4/5 unchanged (classification does not get re-run or
re-derived downstream) — `05_results.gpkg` is simply the only place on disk those per-building
Stage-2 values still live for the **full** population, including the 6 buildings whose
`simulation_status` is `not_simulated` (`la_urban` ×1, `la_rural` ×5 — the same 6 inverted-geometry
buildings OPEN-11/N04 already identified). Using them from there is reading Stage-2 output, not
re-deriving a Stage-5 quantity: `archetype_id`/`levels`/`height_m` are not simulation outputs.

---

## 7. Deliverables

- CSV: `openubem/outputs/comparisons/open10_band_expressibility_fleet.csv` — 7,442 rows, one per
  mapped building: `cell, city, osm_id, archetype_id, simulation_status, levels, height_m,
  num_floors, n_proto, status_shipped, status_proposed_zonegroup` (`status_proposed_zonegroup` is
  populated only for the two `ZoneGroup` archetypes; blank/NaN for the other 14).
- This report.

## How-to-test results

**Does 90 reproduce? — YES**, exactly, per archetype (66 `MidriseApartment` + 24 `HighriseApartment`),
with no adjustment made to land there. Population (7,442 evaluated / 718 excluded) matches the
register exactly, and the shipped code (unmodified `compute_band_map()`/`match_storeys()`) run
against every real fleet `(archetype_id, num_floors)` pair is the sole source of the number — same
population, same code, same definition as the source crosstab. No reconciliation was needed.
