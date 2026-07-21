# T12 — LIVE_SMOKE: layoutGenerator `zone`-mode room_layout on real OSM footprints

Executed 2026-07-02. Read-and-run only; no production code modified by this validation.

## Verdict (RE-VALIDATION after manager fix — 2026-07-02)

**T12 now PASSES all 4 gates.** After the manager's 3-edit fix (degenerate-cell drop
in `_pack_connected_spine`; 5 mm grid-snap + `simplify(0.02)` in the surfaces.py
room_layout→one_zone_per_floor reroute; honest `zoning_strategy` relabel on that
reroute), a full re-run of the same live methodology (real `run_step3` IDFs → E+ 23.1,
no simplified recipe) gives:

| Gate | Target | Result | Pass? |
|---|---|---|---|
| (A) 4 previously-Fatal footprints (503 T, 538 U, 539 U, 549 L) | 0 Fatal | 0 Fatal / 0 Severe on all 4 | ✅ |
| (B) Synthetic bar/L/U/T/O/cross full-annual regression | 0 Fatal / 0 Severe, reroute NO | 0 Fatal / 0 Severe all 6, reroute NO, room-level zoning intact | ✅ |
| (C) la_suburban n=30 zone-mode gen-success | ≥95% | 100% (30/30), 0 `failed_` | ✅ |
| (D) ≤5 real non-rect footprints E+ | 0 Fatal | 0 Fatal / 0 Severe on all 5 | ✅ |

One fidelity caveat (does not block the verdict — see "Observability note" below):
the 4 previously-Fatal footprints no longer Fatal because they now degrade to per-floor
geometry via `generate_layout`'s **area-conservation net** (area drift >1% → return `[]`
→ caller falls back), NOT via the surfaces.py reroute. That area-drift path does not
relabel `zoning_strategy`, so 25/30 rows report `room_layout` while actually building
2-zone (one-zone-per-floor) geometry. Manager edit #3 closed the label gap for the
surfaces.py reroute; the area-drift fallback remains labeled `room_layout`.

---

## Re-validation detail (2026-07-02, post-fix)

### Gate A — 4 previously-Fatal footprints, real production IDFs → E+ 23.1

| osm_id | shape | floors | gen-status | num_zones | E+ | Severe | Warnings |
|---|---|---|---|---|---|---|---|
| way/442340503 | T | 2 | success | 2 | Completed OK | 0 | 217 (was 246 W / 42 Sev / FATAL) |
| way/442340538 | U | 2 | success | 2 | Completed OK | 0 | 208 (was 165 W / 22 Sev / FATAL) |
| way/442340539 | U | 2 | success | 2 | Completed OK | 0 | 150 (was 255 W / 1 Sev / FATAL) |
| way/442340549 | L | 3 | success | 3 | Completed OK | 0 | 334 (was 19 W / 16 Sev / FATAL) |
| way/442340523 | T | 2 | success | 2 | Completed OK | 0 | 152 (was 103,394 W — warning storm also resolved) |

### Gate B — synthetic regression, full-annual E+ 23.1 (T16b/T10 harness, clean box shapes)

| shape | n_zones | n_bsd | reroute fired | E+ | Severe | Warnings |
|---|---|---|---|---|---|---|
| bar | 15 | 102 | no | SUCCESS | 0 | 3,439 |
| L | 45 | 270 | no | SUCCESS | 0 | 25,802 |
| U | 81 | 486 | no | SUCCESS | 0 | 44,574 |
| T | 54 | 324 | no | SUCCESS | 0 | 32,602 |
| O | 144 | 864 | no | SUCCESS | 0 | 92,682 |
| cross | 63 | 378 | no | SUCCESS | 0 | 50,245 |

Clean synthetic shapes keep genuine room-level zoning (15–144 zones, NOT degraded to
per-floor) and never hit the reroute — the fix did not touch the good path.

### Gate C — fresh la_suburban n=30 zone-mode build

- gen-success **30/30 = 100.0%** (was 24/30 = 80%). 0 `failed_interzone_vertex_mismatch`.
- All 30 IDFs re-parse via geomeppy `IDF()` with 0 errors.
- Reroute-fired (surfaces.py `rerouting room_layout to one_zone_per_floor`): **0**.
- 25/30 rows have `num_zones ≤ 2` (degraded to per-floor via the area-drift net);
  18-of-30-that-kept-real-room-layout claim from the pre-fix run no longer holds — the
  degenerate-cell drop is aggressive on these messy footprints, so most la_suburban
  non-rect MidriseApartments now legitimately fall back to per-floor rather than
  produce a broken room layout. This is the intended "degrade gracefully" behavior.

### Gate D — ≤5 real non-rect footprints → E+

Same 5 as Gate A (all real non-rectangular la_suburban MidriseApartments): 0 Fatal /
0 Severe on all 5. Covered by the Gate A table above.

### Observability note (for manager follow-up, non-blocking)

The manifest `zoning_strategy` column reports `room_layout` for all 30 rows, but 25 of
them actually built 2-zone per-floor geometry. The relabel added in builder.py (edit #3)
only fires on the **surfaces.py `intersect_match` reroute**, which fired 0 times here.
The footprints instead fell back one layer earlier, inside `generate_layout` (area-drift
`> 1%` → returns `[]` → `build_zones` degrades to one_zone_per_floor), and that path
leaves the strategy label as `room_layout`. If accurate strategy accounting matters for
downstream reporting, the area-drift fallback needs the same relabel. E+ correctness is
unaffected.

---

## Original findings (2026-07-02, PRE-FIX — retained for the record)

**T12 did NOT pass (pre-fix).** Real, messy MidriseApartment footprints exist in the
phaseE fixtures (434 non-rectangular across 9/12 cells), so the recon precondition is met.
But gen-success on a 30-building working set was **80%** (target ≥95%), and — more
importantly — **4 of 5 real production IDFs that DID report `generation_status=success`
and parsed cleanly with geomeppy `IDF()` FATAL when actually run through EnergyPlus
23.1.** This was a real bug the LIVE_SMOKE was designed to surface: the existing IDF-parse
check is not sufficient to guarantee E+ can simulate the geometry.

---

## Step 1 — Recon (all 12 phaseE cells, MidriseApartment only)

| cell | total bldgs | MidriseApartment | COMPACT | SLAB | POINT | RIBBON | IRREGULAR | L | U | T | CROSS | O |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| austin_centre | 413 | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| austin_rural | 245 | 18 | 14 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| austin_suburban | 437 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| austin_urban | 425 | 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 0 |
| la_centre | 226 | 14 | 3 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 4 | 4 |
| la_rural | 149 | 10 | 0 | 0 | 1 | 7 | 1 | 0 | 0 | 0 | 1 | 0 |
| **la_suburban** | 1343 | **1283** | 25 | 0 | 80 | 893 | 57 | **63** | **87** | **46** | **23** | **9** |
| **la_urban** | 618 | **446** | 57 | 35 | 25 | 148 | 30 | 22 | 31 | 5 | 56 | 37 |
| nyc_centre | 738 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| nyc_rural | 198 | 22 | 5 | 0 | 0 | 10 | 4 | 0 | 0 | 0 | 3 | 0 |
| nyc_suburban | 1589 | 979 | 2 | 0 | 9 | 963 | 1 | 2 | 2 | 0 | 0 | 0 |
| nyc_urban | 1779 | 30 | 2 | 0 | 0 | 0 | 3 | 1 | 2 | 3 | 19 | 0 |
| **TOTAL** | 9160 | 2821 | 114 | 39 | 115 | 2022 | 97 | 89 | 123 | 54 | 117 | 51 |

**Non-rectangular (L/U/T/CROSS/O) total: 434 / 2821 MidriseApartments (15.4%)**, present in
9 of 12 cells. Richest: `la_suburban` (228 non-rect), `la_urban` (151 non-rect). Recon
CSV: `t12_recon_classified.csv` (scratchpad).

Recon precondition is satisfied — the live path genuinely exercises L/U/T/CROSS/O
geometry, not just synthetic boxes.

---

## Step 2 — Zone-mode build smoke (`la_suburban`, n=30: 24 non-rect + 6 compact controls)

Ran `run_step3(gdf, {}, tmp_dir, resolution_mode="zone")` — the real production path.

- **gen-success: 24/30 = 80.0%** (target ≥95% — **NOT MET**)
- 6 failures, all `failed_interzone_vertex_mismatch` (builder.py's post-extrude
  gate drops the building entirely rather than producing a bad IDF):
  `way/442340567` (CROSS), `way/442340622` (T), `way/442340634` (T),
  `way/442340642` (U), `way/442340643` (U), `way/442340646` (T)
- All 24 successful IDFs re-parsed via geomeppy `IDF()` with 0 errors.
- `zoning_strategy` column reports `room_layout` for all 30 rows (including the 6
  failures) — this field does **not** reflect an internal fallback that happens a
  layer lower: 6 of the 24 "successes" silently degraded to a 2-zone
  one-zone-per-floor geometry inside `extrude_geometry()` (surfaces.py's own
  `intersect_match raised IndexError → rerouting to one_zone_per_floor`, logged at
  `openubem/idf/surfaces.py:623`), distinct from builder.py's own outer reroute
  gate. Real room-level layouts (tens to hundreds of zones) were kept for the other 18.
- Manifest CSV: `t12_build_smoke_manifest.csv` (scratchpad).

---

## Step 3 — E+ 23.1 Fatal/Severe check on the REAL production IDFs

Rather than rebuild a simplified standalone recipe (which risks missing steps the
real pipeline performs), I ran EnergyPlus 23.1 directly against the actual IDFs
`run_step3` produced in Step 2 for 5 real non-rectangular footprints (osm_id,
cell=la_suburban, real `levels`-derived floor count):

| osm_id | shape | floors | build gen-status | E+ result | Severe | Fatal message (verbatim, truncated) |
|---|---|---|---|---|---|---|
| way/442340503 | T | 2 | success | **FATAL** | 42 | `Temperature (low) out of bounds [-871.87] for zone="WAY/442340503_F1_W0C7", for surface="BLOCK WAY/442340503_W0C7 STOREY 1 FLOOR 0001_1"` → `Program terminates due to preceding condition.` |
| way/442340538 | U | 2 | success | **FATAL** | 22 | `RoofCeiling:Detailed="BLOCK WAY/442340538_WHOLE STOREY 0 CEILING 0001_1", Vertex size mismatch between base surface ... and outside boundary surface: BLOCK WAY/442340538_WHOLE STOREY 1 FLOOR 0001_1. The vertex sizes are 38 for base surface and 41 for outside boundary surface.` → `GetSurfaceData: Errors discovered, program terminates.` |
| way/442340549 | L | 3 | success | **FATAL** | 16 | `CheckConvexity: Surface="BLOCK WAY/442340549_WHOLE STOREY 2 WALL 0019 WINDOW" is non-planar.` → `GetSurfaceData: Errors discovered, program terminates.` |
| way/442340523 | T | 2 | success | ok (no Fatal) | 0 | N/A — completed successfully, but with **103,394 Warnings** (5m56s runtime vs <2s for the others — likely a recurring-warning storm, worth a separate look) |
| way/442340539 | U | 2 | success | **FATAL** | 1 | `CalcHeatBalanceInsideSurf: The temperature of -4594594.73 C for zone="WAY/442340539_F1_W0U4", for surface="BLOCK WAY/442340539_W0U4 STOREY 1 FLOOR 0001_1" ..is very far out of bounds during warmup. This may be an indication of a malformed zone.` → `Program terminates due to preceding condition.` |

**4 of 5 real, non-rectangular, `generation_status=success` production IDFs are
E+ Fatal (0 Fatal target NOT MET).** Full `.err` files are preserved at
`t12_real_idf_runs\<osm_id>\eplusout.err` (scratchpad) for follow-up debugging.

Two distinct failure signatures observed:
1. **Vertex-count / non-planar surface mismatches** on paired horizontal surfaces
   (floor/ceiling, window) — `way/442340538`, `way/442340549` — consistent with the
   room_layout → one_zone_per_floor internal reroute (surfaces.py:623) not being
   fully repaired before the IDF is saved.
2. **Malformed-zone temperature blowups during warmup/sizing**
   (`-871.87`, `-4594594.73`) — `way/442340503`, `way/442340539` — these pass
   geometry-parse checks but are thermodynamically degenerate (likely a
   near-zero-area or badly-connected zone slipping through).

A cross-check with a simplified standalone recipe (generate_layout → extrude_geometry
→ set_default_constructions → minimal loads/HVAC/DHW, no `assign_constructions`/
`set_adiabatic_surfaces`/`assign_infiltration`) reproduced the **same** Fatal pattern on
all 5, confirming this is not an artifact of the real pipeline's extra steps — the
underlying geometry itself is broken. Scratchpad script: `t12_ep_smoke.py`;
results: `t12_ep_smoke_results.csv`.

---

## Caveats

- Sample is limited to `la_suburban` (30 build-smoke buildings, 5 E+ buildings) —
  richest cell for non-rect MidriseApartment, but failure rate may differ in other
  cells (`la_urban`, `nyc_urban`, etc.).
- The `zoning_strategy` manifest column does not distinguish genuine room_layout
  builds from internally-rerouted-and-recovered one_zone_per_floor builds — a
  manifest-fidelity gap the manager may want tracked separately.
- `way/442340523`'s 103,394-warning "success" run is suspicious even though it
  didn't Fatal — worth a look before calling any of these 5 clean.

## Scratchpad files created (none touch `openubem/`, `tests/`, or `docs/` other than this output artifact)

- `t12_recon.py`, `t12_recon_classified.csv` — Step 1 recon
- `t12_build_smoke.py`, `t12_build_smoke_manifest.csv`, `t12_zone_build\` (IDFs) — Step 2
- `t12_ep_smoke.py`, `t12_ep_smoke_results.csv`, `t12_ep_runs\` — Step 3 standalone-recipe cross-check
- `t12_run_real_idfs.py`, `t12_real_idf_runs\` — Step 3 real-production-IDF E+ runs (primary evidence)
