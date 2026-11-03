# MEASUREMENT — OPEN-42: what the zoning step does to these six buildings

**Date:** 2026-08-18 · **Task:** T05 of `PLAN_five-items-2026-08-18.md`

## 0. Verdict up front

**Partial mechanism found, reported honestly as partial.** The `.eio`'s `Zone Information` records
answer the plan's own diagnostic question ("is the blow-up zone the degenerate one, or an ordinary
one?") cleanly: **it is an ordinary zone.** In 15 of the 16 fatal runs, the zone named in the run's own
`Temperature (low|high) out of bounds` Severe is on the **topmost floor** of the building, and its
floor area, volume, ceiling height, and horizontal extents are **byte-identical** to its own
non-fatal sibling zones on the lower floors of the same run. Nothing about its *shape* is unusual —
only its *position* differs.

**What the `.eio` does NOT deliver is a single numeric statistic, from the fields it carries, that
cleanly separates all 16 failing runs from the 14 succeeding ones.** Two candidate statistics were
tested against the required 20-building background control and **both failed the control**:
"reported Volume inconsistent with Floor Area × Ceiling Height" looked promising on the target
population alone, but the control caught it — the same signature is common (12 of 20 background
buildings, all succeeding) and is therefore not predictive. Raw zone-size/aspect-ratio statistics
(floor area, footprint diagonal, aspect ratio) do not separate the 16 fatal zones from the background
successful population either — most fatal zones sit comfortably inside the background's own
distribution.

**Per the plan's own permitted outcome:** the deeper "why does the topmost real-footprint zone go
unstable for these six buildings but not for 20 ordinary ones" is **not determinable from
`eplusout.eio` alone** — the `Zone Information` record does not carry a field that captures the thing
that is actually different (most plausibly the building's own surface geometry/winding, which is an
OPEN-11 fact already on record for exactly this population — see §5). This is reported as the honest
result, not smoothed into a stronger claim than the data supports.

---

## 1. Method

`scripts/analysis/open42_zone_geometry.py`, read-only over the local E02 harvest
(`C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest`). For each of the 30 (building, mode) runs in
`openubem/outputs/comparisons/open42_six_failure_causes.csv`, parses every `Zone Information` line in
that run's `eplusout.eio` into one row per zone (`zone_name`, floor area, volume, ceiling height,
min/max X/Y/Z, plus derived `volume_over_floor_area`, `volume_consistency_ratio` = that value divided
by ceiling height (should be ≈1.0 if the reported Volume is internally consistent with Floor Area ×
Ceiling Height), `aspect_ratio`, `footprint_diagonal_m`, and `floor_index`/`is_top_floor_zone` parsed
from the `_F<n>_` zone-name suffix). Joined to outcome via `open42_six_failure_causes.csv` on
`(cell, stem, mode)`.

**Row-count check: 30/30 runs had zones parsed — no missing runs.**

**Blow-up zone identification, cross-checked two ways:** primary source is the zone name embedded in
`open42_six_failure_causes.csv`'s own `severe_line_text` (the Severe immediately preceding each run's
Fatal termination — already-established, authoritative per-run evidence from OPEN-42's own prior
measurement). A second, independent re-read of each run's raw `eplusout.err` (grabbing the *first*
`Temperature ... out of bounds ... zone=` line in the file) was run as a cross-check: it disagreed with
the CSV on exactly 1 of 16 runs (`la_rural/way_472961091/fast_zone`: CSV names
`WAY/472961091_F2_PERIM6`, the first-in-file line names `WAY/472961091_F1_PERIM6` — the run logged
more than one such Severe before the one immediately preceding its Fatal; the CSV's is treated as
authoritative, and the discrepancy is reported here rather than hidden). All 16 fatal runs' blow-up
zones were found (16/16).

**Background control (plan step 3, required):** 20 buildings that succeed (`Completed Successfully`)
in **all five modes** — 10 from `la_rural`, 10 from `la_urban` (the same two cells as the six target
buildings), excluding the six target stems. Selected buildings:
`la_rural`: `way_222366800, way_472960895, way_472960930, way_472960931, way_472960932, way_472960933,
way_472960934, way_472960935, way_472960936, way_472960937`.
`la_urban`: `relation_6243355, relation_6353541, relation_6356829, relation_6356830, relation_6356862,
relation_6356884, relation_6356886, relation_6356887, relation_6378549, relation_6378550`.
Zones parsed for all 20 × 5 = 100 background runs (600 zone rows).

**Output:** `openubem/outputs/comparisons/open42_zone_geometry.csv` — 1,011 rows (411 target zone rows
across 30 runs + 600 background zone rows across 100 runs).

---

## 2. Is the blow-up zone the degenerate one, or an ordinary one? (plan step 2)

**Ordinary — for 15 of 16 fatal runs.** All five `la_rural` buildings, across all three per-floor-
real-footprint modes (`auto`, `fast_zone`, `floor`), fail on their topmost floor's zone
(`_F2_...`, since these are 3-storey buildings), and that zone's `volume_consistency_ratio` sits at
0.997–1.000 — i.e. its reported Volume is exactly what Floor Area × Ceiling Height predicts, and its
floor area/volume/ceiling-height are numerically identical to its own non-fatal siblings one and two
floors below in the same run (verified directly, e.g. `way_472960972`'s `_F0_CORE`, `_F1_CORE`, and
`_F2_CORE` all report floor area 2,221.44 m², volume 7,775.03 m³, ceiling height 3.50 m — only `_F2`
fails):

| cell | stem | mode | blow-up zone | aspect_ratio | floor_area (m²) | volume_consistency_ratio | topmost floor? |
|---|---|---|---|---|---|---|---|
| la_rural | way_472960972 | auto | `_F2_CORE` | 1.78 | 2221.44 | 1.000 | yes |
| la_rural | way_472960972 | fast_zone | `_F2_PERIM10` | 1.02 | 3.10 | 0.999 | yes |
| la_rural | way_472960972 | floor | `_F2_WHOLE` | 1.70 | 3417.58 | 1.000 | yes |
| la_rural | way_472961034 | auto | `_F2_CORE` | 1.35 | 783.79 | 1.000 | yes |
| la_rural | way_472961034 | fast_zone | `_F2_PERIM5` | 5.60 | 1.29 | 0.997 | yes |
| la_rural | way_472961034 | floor | `_F2_WHOLE` | 1.32 | 1398.50 | 1.000 | yes |
| la_rural | way_472961088 | auto | `_F2_CORE` | 1.19 | 907.13 | 1.000 | yes |
| la_rural | way_472961088 | fast_zone | `_F2_PERIM6` | 10.72 | 0.82 | 1.000 | yes |
| la_rural | way_472961088 | floor | `_F2_WHOLE` | 1.20 | 1555.88 | 1.000 | yes |
| la_rural | way_472961091 | auto | `_F2_CORE` | 1.41 | 750.28 | 1.000 | yes |
| la_rural | way_472961091 | fast_zone | `_F2_PERIM6` | 10.04 | 0.85 | 0.998 | yes |
| la_rural | way_472961091 | floor | `_F2_WHOLE` | 1.36 | 1355.23 | 1.000 | yes |
| la_rural | way_472961171 | auto | `_F2_CORE` | 3.07 | 19057.63 | 1.000 | yes |
| la_rural | way_472961171 | fast_zone | `_F2_CORE` | 3.07 | 19057.63 | 1.000 | yes |
| la_rural | way_472961171 | floor | `_F2_WHOLE` | 2.79 | 22443.66 | 1.000 | yes |
| la_urban | way_402215469 | auto | `_F3_WHOLE` | 1.27 | 1179.64 | **0.0024** | **no** (F3 of 6; top is F5) |

**15/16 (94%) on the topmost floor.** The one exception — `la_urban/way_402215469/auto` — fails on
`_F3_WHOLE`, the fourth of six floors (F0–F5), not the top. That same run shows a large,
**uniform-across-every-zone** volume anomaly (§3), unlike the other 15.

---

## 3. Candidate statistic tested and ruled out: Volume/Floor-Area/Height inconsistency

`la_urban/way_402215469`'s `auto`-mode run stood out: **every one of its 6 zones** reports
`Volume = 10.00 m³`, regardless of Floor Area (1,179.64 m² per floor) — a ~400× discrepancy from the
~4,128.7 m³ that Floor Area × Ceiling Height implies, and exactly what the *same building's*
`fast_zone`/`floor` modes (which succeed) report correctly (4,128.73 m³). This looked like a strong
candidate mechanism.

**The background control disproves it as a general predictor.** Checked whether any of the 20
background buildings show the same signature (every zone in a run reporting `Volume ≈ 10.00 m³`
independent of floor area) in their own `auto`-mode runs:

**12 of the 20 background buildings (60%) show exactly this pattern in `auto` mode — and all 12
succeed.** (`way_472960933`, `way_472960935`, and all 10 of the sampled `la_urban` `relation_*`
buildings.) This is evidently a general artifact of how `auto` mode reports the `Volume` field for
some zone shapes — not a failure signal. **Statistic ruled out, reported rather than silently
discarded**, because it is exactly the kind of "plausible story" the background control exists to
catch.

A looser, per-zone version of the same idea (`volume_consistency_ratio` outside [0.9, 1.1], applied to
all `PERIM`/`CORE`/`WHOLE` zones in the three per-floor modes) is equally uninformative: **156 of 387
target per-floor-mode zones (40%)** and **97 of 286 background per-floor-mode zones (34%)** fall
outside that band — nearly identical proportions in the failing and non-failing populations. This is a
known, common artifact of how `auto`/`fast_zone` compute perimeter-strip zone volumes for
non-rectangular footprints, present at essentially the same rate whether the run fails or not — not a
separator.

---

## 4. Candidate statistic tested and ruled out: raw zone size / shape

Checked whether the 16 fatal zones are simply *larger* or more *elongated* than a typical successful
topmost-floor zone. Background topmost-floor zones (same three per-floor modes, `n=76`) span aspect
ratio 1.02–4.69 and footprint diagonal 12.5–142.0 m. The 16 fatal zones span aspect ratio 1.02–10.72
and footprint diagonal 6.5–299.3 m — **mostly inside the background's own range**, with only one
building (`way_472961171`, floor area up to 22,443.66 m², diagonal up to 299.3 m) clearly above the
background's maximum. No single size or aspect-ratio threshold separates the 16 from the 14 without
misclassifying a large share of the background sample. **Ruled out as a general separator.**

---

## 5. What the position finding does and does not establish

**Established, with the required background control:** among these six buildings, the zoning modes
that decompose the building into explicit per-floor zones matching its real OSM footprint (`auto`,
`fast_zone`, `floor`) place the topmost floor's zone directly under the roof with no zone above it for
thermal buffering, and it is specifically that zone that fails 15 times out of 16. Zoning modes that
never construct such a zone — `building` (one lumped zone spanning every floor) and `layout_assign`
(fixed DOE-prototype template zones, e.g. `ZONE1 OFFICE`/`ZONE2 FINE STORAGE`/`ZONE3 BULK STORAGE`
with `Zone Multiplier=3`, entirely unrelated to the real footprint) — never fail for any of these six
buildings (0/12 runs). Among the 18 per-floor-zoned runs specifically, 16 fail and 2 succeed
(`la_urban`'s `fast_zone` and `floor` runs) — and even those 2 "successes" show a *non-fatal* Severe on
their own topmost zone (`_F5_WHOLE`), consistent with the same positional effect operating below the
threshold that triggers a Fatal termination there.

**Not established, and explicitly not claimed:** why the topmost real-footprint zone is unstable for
*these* six buildings specifically, when the 20 background buildings' own topmost real-footprint zones
— structurally the same kind of zone, sitting in the same position — do not fail. Nothing in `Zone
Information` (floor area, volume, ceiling height, extents, aspect ratio) distinguishes the two
populations. **Per the plan's own permitted outcome: this is "not determinable from `eplusout.eio`."**

---

## 6. Connection to OPEN-11 (context, not re-derived here)

All six of these buildings are the same six OPEN-11 "inverted-geometry" buildings (5 `la_rural`
Warehouse + 1 `la_urban` Warehouse, `way/472960972, way/472961034, way/472961088, way/472961091,
way/472961171, way/402215469`) that N04
(`MEASUREMENT_open-06-07-11_failure-population.md` §3) already confirmed are the same population that
historically required an "orient + thermal-mass fallback" (T13/T06-R, 2026-06-27) to recover, and that
the automated E-R3-3 re-run subsequently dropped back to `not_simulated` because it does not invoke
that fallback. A surface-winding/orientation defect specific to these six buildings' raw geometry — not
a `Zone Information`-visible property — is the most plausible remaining candidate for "why the topmost
zone specifically" (a winding defect would most directly affect roof-facing surfaces, which only the
topmost zone owns), but confirming that would require reading per-surface data (`Surface Details`,
`HeatTransfer Surface Facing` etc. — not `Zone Information`) or the `in.idf` geometry itself, both out
of this task's `.eio`-only scope. This is noted as the most likely next step, not performed here.

---

## 7. Closure recommendation

**OPEN-42 sharpens but does not close.** New, evidenced facts added to the record:
1. The blow-up zone is ordinary in shape (byte-identical to its own non-fatal siblings), not
   geometrically degenerate — settled with high confidence (15/16 direct sibling comparisons).
2. It is the topmost floor's zone in 15/16 fatal runs — a genuine, quantified positional pattern,
   though not a perfect 16/16 separator.
3. Two plausible-looking statistics (Volume/FloorArea/Height inconsistency; raw zone size/aspect) were
   tested against a required 20-building background control and **both failed the control** — ruled
   out explicitly rather than left as unverified stories.
4. The remaining "why" is not determinable from `eplusout.eio`; the most likely next artifact is
   per-surface geometry (`in.idf` or `.eio` `Surface Details`), tying back to OPEN-11's known
   winding/orientation defect for this exact population — named as the next step, not pursued here
   (out of this task's scope, no simulation/IDF regeneration performed).

---

## 8. Artifacts

- `scripts/analysis/open42_zone_geometry.py`
- `openubem/outputs/comparisons/open42_zone_geometry.csv` (1,011 rows: 411 target zone rows across the
  30 runs + 600 background zone rows across 100 runs for 20 background buildings)
- This report.

**No fix, no code change, no simulation. Diagnosis only, per the diagnose-before-remediate rule.**
