# T22 — LIVE_SMOKE results: Stage 6 (UTCI / outdoor microclimate) on `nyc_centre`

**Plan reference:** `docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md` §7 T22.
**Run date:** 2026-07-24. **Git commit:** `961cff3805166c4d0715e44db9d853f2f2fbd735`.
**Source cell (read-only):** `docs/docs_VALIDATION/validations/overAll/results/phaseE/nyc_centre/`
**Output (never written into the source cell — see PLAN §9 T18 progress-log entry, deviation 1):**
`openubem/outputs/stage6/nyc_centre/` (default tiers) and
`openubem/outputs/stage6/nyc_centre_tier2wind_osm/` (macdonald wind + osm vegetation).

> **Headline finding first, per this arc's own discipline of not burying a real gate failure:**
> the second (higher-tier) run surfaced a genuine, serious defect in T15's `macdonald` wind tier —
> physically impossible wind speeds (up to ~400,000 m/s) at a non-trivial fraction of cells near
> real (tall) buildings. Root-caused and written up as **E-UTCI-07** (plan §10). The default tier
> (`cost730`), and everything CP-1 through CP-3 already signed, is unaffected. See §4 below.
>
> **Current status (updated 2026-07-24, after the E-UTCI-08 fix): RESOLVED.** §4/§6/§7/§8 below
> describe the original defect and the first (E-UTCI-07) fix attempt, left unedited per this
> document's own "a silent correction is indistinguishable from a mistake" rule (§8's own text).
> **§9 is the current, final status**: after a second, independently-adjudicated fix (E-UTCI-08),
> the macdonald tier is now verified **zero** `0<=v_1p1<=v10` bound violations, domain-wide, on
> this real domain — checked directly against the on-disk raster, not inferred. Read §9 first if
> you only read one section.

---

## 1. What ran

| | Run 1 (default tiers) | Run 2 (higher tiers) |
|---|---|---|
| `vegetation_tier` | `none` (honest gap — no real canopy data assumed) | `osm` — **185 real OSM green-space polygons** (parks/gardens/wood/scrub/grass), fetched live via `openubem/viz/context_features.py::generate_context_features` for this run only, passed as `canopy_gdf` |
| `wall_temp_tier` | `empirical` | `empirical` (Tier-2 EnergyPlus coupling not exercised in T22 — the plan's own T22 "How" does not name it; see PLAN §9 T18 deviation 4) |
| `wind_tier` | `cost730` | `macdonald` — **see the headline finding above; do not treat this run's wind field as valid** |
| `ta_tier` | `tier0` (uniform EPW dry-bulb) | `tier0` |
| `res_m` / `buffer_m` | 2.0 m / 200.0 m | 2.0 m / 200.0 m |
| `window_mode` | `hottest_week` | `hottest_week` |

Both runs resolved the buildings file via the F-15 fallback (`01_buildings.gpkg`, not `_clean`) and
the EPW via **step 3 of F-16's ladder** — re-resolved from the building centroid against the global
cache (`epw_resolution_step = "cache_resolved:station=725053:dist_km=2.9"`), landing on
**station 725053, New York–Central Park Obs–Belvedere Castle** (2.9 km from the buildings'
centroid), exactly the station F-16/T22 expected. The archived cell has no `weather/` subdirectory,
confirming that trap is real and the fallback works.

---

## 2. Buildings, domain, and the honest height gap (F-18)

- **738 buildings**, EPSG:32618. **121 excluded from the DSM for missing `height_m` (16.4%)** —
  an exact match to F-18's own pre-measured number. Their footprints still mask the UTCI output
  (they read as building interior / nodata everywhere); no height was invented to close the gap.
- **Domain shape: 896 × 983 cells** at 2 m resolution, 200 m buffer — matches CP-2/CP-3's own
  prior measurement on this same domain exactly (same buildings file, same config defaults).
- `dem_source = "assumed_flat"` (no user DEM supplied — an honest, flagged assumption, not a
  silent default).
- Mean SVF outside building footprints: **0.873** — a high figure, reflecting that the 200 m
  buffer around this specific footprint cluster includes substantial open space (streets, a
  visible water body in the five-panel figure below, and low-density blocks), not that the whole
  domain is architecturally open.

---

## 3. The window and the EPW's own weather (real data, not synthetic)

`hottest_week` selected **2001-07-18 16:00 through 2001-07-25 15:00** (168 h) — the contiguous
week maximising mean dry-bulb in the resolved TMYx file. Across that week the EPW's own dry-bulb
ranged **20.0 – 33.9 °C**, `v10` and `wind_direction_deg` varied hour to hour (real data, not
constant), and **100% of hours used the EPW's own measured horizontal-infrared field for `L_sky`**
(`used_measured_l_sky_hour_fraction = 1.0`) — the Prata fallback was never needed for this window.

---

## 4. 🔴 E-UTCI-07 — the macdonald wind tier defect (full detail in plan §10)

The second run's `06_mc_wind_1p1m_hourly.tif` contains values from **-353,987.5 to +834,439.4
m/s**. Root-caused to a domain-validity violation in T15's Macdonald (1998) formula: it
extrapolates the standard **10 m** reference wind down to canopy height `H` assuming `H` (and the
derived displacement height `d`) stay below 10 m — an assumption `nyc_centre`'s real building
stock breaks routinely (mean height 41.9 m, max 397 m; two-thirds of near-building cells have
`mean_height_m > 10 m`). When the independently-derived roughness length `z0` happens to land
close to the code's own `max(10-d, 1.1)` floor, the log-law's denominator approaches zero and the
formula divides by (near) nothing.

**Quantified on this real domain:** 0.62% of all cells, 1.3% of near-building cells, show
`|v| > 50 m/s`; 6.3% of near-building cells show `|v| > 10 m/s` (already unphysical for a
downscaled ≤5 m/s reference wind). **This is not new to T22** — the *already-signed-off* T15 unit
test's own "near block" point independently reproduces `-19.06 m/s` (a negative wind speed) once
printed rather than only compared against the test's own weak `< free_stream` assertion. The
defect was latent since T15; T22 is what made it visible.

**Consequence for this write-up:**
- The macdonald run's `06_mc_wind_1p1m_hourly.tif` is **not reported as a valid pedestrian wind
  field** below.
- Its wind-clamp statistic (**43.4% of cell-hours**, vs. the default run's clean **26.8%**) is
  **not** reported as "macdonald reduces wind near buildings more than cost730" — that would be
  reporting a confounded number as a physical finding. It is stated here only as a measured
  artifact of the defect.
- The macdonald run's UTCI numbers **are not merely "resting on a bad input" — they contain a
  measured, non-trivial, spatially-patterned error of their own.** `va10_eq`'s `[0.5, 17.0]` clamp
  keeps the polynomial from seeing a literal 5-digit wind speed, but it lands at **either** the
  floor or the ceiling depending on the blow-up's sign, and the polynomial is strongly
  wind-sensitive (P-06). Directly comparing the two runs' `06_mc_utci_mean.tif`
  (`06_mc_t22_tier_comparison_utci_mean.png`, §6) shows **visible, ring-shaped cold bands hugging
  building footprints in the macdonald run that do not exist in the default run**: 4.44% of
  outside-building cells drop by more than 1 °C, 1.25% by more than 3 °C, the worst single cell by
  **7.94 °C** (28.43 → 20.49 °C — crossing an entire stress class, from "Moderate heat stress" to
  "No thermal stress"). A reader could easily mistake this for a real "wind speeds up around
  building corners and cools pedestrians" effect. **It is not — it is this defect's artifact.**
  See plan §10 E-UTCI-07 for the full disposition and the candidate fixes not yet adjudicated.
- The default run (`cost730`) never touches this code path and is fully valid.

---

## 5. Default-tier run — the reportable LIVE_SMOKE result

### 5.1 Runtime, memory, output size

- **Wall-clock: 898.8 s (~15.0 min)** end to end (buildings → EPW → domain → SVF → 168-hour loop
  → exposure → manifest), of which the static SVF/horizon computation is the dominant one-time
  cost — consistent with CP-2/CP-3's own prior measurement (~507–536 s) on this identical domain,
  paid once (§4.9), not per hour.
- **Peak RAM: not instrumented with a profiler this session** — reported qualitatively instead of
  invented precisely (rule 14). The dominant in-memory structure is the full-window UTCI stack
  (`168 × 896 × 983 × 4 bytes ≈ 597 MB`, held because T20's PHEH/CTSI need the whole window at
  once — PLAN §9 T18 deviation 5); `Tmrt`/`v(1.1m)`/`Ta`/flags stream band-by-band to disk rather
  than accumulating the same way. Spot-checked `WorkingSet` during the run (Windows
  `Get-Process`) sat in the **390–420 MB** range during the SVF phase; total peak is expected
  somewhat higher during the UTCI-stack/exposure tail, order **0.8–1.2 GB**, not multiple GB.
- **Output size: 715.3 MB total** for this one cell/window/resolution combination — dominated by
  the two full hourly stacks (`06_mc_tmrt_hourly.tif` 355.1 MB, `06_mc_utci_hourly.tif` 330.9 MB).
  This is the real cost §4.9's analysis-window scoping decision exists to bound: the annual
  equivalent (52×) would be tens of GB per cell.

### 5.2 Field ranges (outside building interiors, whole 168 h window)

| Field | Min | Mean | Max |
|---|---|---|---|
| `Ta` (Tier-0, EPW dry-bulb) | 20.0 °C | 27.2 °C | 33.9 °C |
| `Tmrt` | **7.13 °C** | 34.7 °C | 69.76 °C |
| `v(1.1 m)` (cost730) | 0.0 m/s | 1.12 m/s | 3.88 m/s |
| `UTCI` (`06_mc_utci_peak.tif`, per-cell max over the window) | 34.76 °C | — | 44.64 °C |
| `UTCI` (`06_mc_utci_mean.tif`, per-cell mean over the window) | 25.11 °C | — | 29.18 °C |

**The `Tmrt` minimum (7.13 °C, vs. `Ta`'s own minimum of 20.0 °C — a ~13 °C deficit) is a real,
expected manifestation of the already-adjudicated E-UTCI-06 finding**, not a new defect: this
model family (Höppe 1992 6-directional weighting, same as SOLWEIG/RayMan/ENVI-met) is
peer-reviewed-documented (Gál 2020) to under-predict nighttime `Tmrt` by 2–10 °C vs. measurement,
and this run used the EPW's own **measured** horizontal-infrared field 100% of hours (§3) — a
genuinely cold clear-sky night in the real weather file, applied through the same corrected
`Psi_grd=0.50` weighting E-UTCI-04 fixed. Well inside `test_night_tmrt_close_to_ta`'s own
regression backstop (`delta >= -25 °C`).

`UTCI` peak's own distribution is tightly clustered near its maximum (p50 = 44.54 °C, p95 =
44.62 °C, max = 44.64 °C, while the minimum sits at 34.76 °C) — meaning **the majority of the
domain's open/unshaded cells reach a nearly identical peak UTCI at the single hottest, sunniest
hour of the week**, and only the minority of cells in persistent building shade have a materially
lower peak. This is a real, explainable consequence of this specific footprint cluster's
geometry (a large fraction of open ground within the 200 m buffer), not an artifact.

**Stress-class breakdown, `06_mc_utci_mean.tif` (week-average, outside buildings):**

| Class | Area share |
|---|---|
| No thermal stress | 1.84% |
| Moderate heat stress | 98.16% |

**Stress-class breakdown at the hottest hour of the week (2001-07-19 12:00 local) is in §5.4**,
alongside the reference figure it belongs with.

Even a hot NYC July week never crossed the **Extreme heat stress (>46 °C)** boundary at this
resolution/tier: `area_hours_extreme_heat_m2h = 0.0` (PHEH's honest area-hours field name, no
population raster available — §7).

### 5.3 Clamp-flag statistics (default run, clean — not confounded by E-UTCI-07)

- **Wind clamp: 39,634,560 / 147,969,024 cell-hours = 26.8%.** Expected and reported, not hidden
  (U05 §2.2 line 80): dense urban geometry and real calm hours in this EPW file routinely produce
  `v(1.1 m)` below the polynomial's 0.5 m/s floor.
- **Ta Tier-1 clamp: 0** — expected exactly, `ta_tier="tier0"` never exercises that clamp path.
- **UTCI polynomial's own 4 clamp flags (Ta/Tmrt/wind/vapour bounds, P-01): all zero across the
  entire run.** Every input stayed inside `[-50,50]`/`[-30,70]`/`[0.5,17]`/`[0,5 kPa]` — the wind
  bound never fires at the polynomial itself because `wind.py`'s own clamp already enforces
  `[0.5,17]` before the value reaches `utci_approx` (the two clamps are layered by design, §4.2).

> **Where the figures live** (re-organised by the user, 2026-07-25). The canonical flat home is
> `openubem/outputs/` per the standing project rule. The `docs_ACTIVE` copies moved out of
> `implementation/` into a dedicated split — **`docs/docs_DONE/OUTDOOR/UTCI/results/UTCI-maps/`** for the
> spatial/raster panels (`06_mc_cp3_four_panel`, `06_mc_t22_five_panel`, `06_mc_svf`,
> `06_mc_shadow_noon`, `06_mc_t22_tier_comparison_utci_mean`) and
> **`docs/docs_DONE/OUTDOOR/UTCI/results/UTCI-figures/`** for the plotted charts
> (`06_mc_t22_diurnal_curve`, both `06_mc_t22_stress_histogram_*`). Every `openubem/outputs/...png`
> path named below is still correct; only the `docs_ACTIVE` copy location changed.
>
> **This document moved with them** — it now lives at
> `docs/docs_DONE/OUTDOOR/UTCI/results/OpenUBEM_results_UTCI_microclimate.md`, no longer under
> `implementation/`. The arc plan, the outdoor-analysis registry and `PROJECT_CHECKLIST.md` were
> updated to point here on 2026-07-25.

### 5.4 The reference figure — real data, first time

`openubem/outputs/06_mc_t22_five_panel_nyc_centre.png` (docs copy:
`docs/docs_DONE/OUTDOOR/UTCI/results/UTCI-maps/`), at **2001-07-19 12:00 local** (the peak-`Ta`, hottest
hour of the whole window, `Ta = 33.9 °C`): real NYC block/street geometry is visible in every
panel; `Tmrt` shows the expected canyon-shadow pattern (dark, cooler street interiors against
bright, hot sunlit roofs and open ground); the UTCI panel is dominated by "Very strong heat
stress" (red) with a visible "Strong heat stress" (orange) band in shaded streets — directly
comparable in layout and physical pattern to `1784462193769.jpg`. **`v(1.1 m)` and `Ta`/`e` render
as flat single-colour panels at this specific hour** — verified, not a rendering bug: the EPW's
own wind speed is **exactly 0.0 m/s** at 2001-07-19 12:00 (confirmed directly from the raster),
the same genuinely-calm-hour pattern CP-3 already documented for a different hour in this same
resolved TMYx file, and `Ta`/`e` are spatially uniform by Tier-0/Tier-0 design.

`openubem/outputs/06_mc_t22_stress_histogram_nyc_centre.png` — area per stress class at the same
hour: **Strong heat stress ~0.15 km², Very strong heat stress ~2.53 km²**, no cell in Moderate or
below — consistent with, and hotter than, the earlier hourly snapshot, since this is the single
hottest hour of the week by air temperature.

`openubem/outputs/06_mc_t22_stress_histogram_window_peak.png` — the same breakdown for
`06_mc_utci_peak.tif` (each cell's own maximum over the full 168 h, not one shared hour): shows
what the worst moment of the week looked like **per cell**, which is hotter and more concentrated
in "Very strong heat stress" than any single shared hour, because different cells peak at
different hours (e.g., an east-facing street peaks in the morning, a west-facing one in the
afternoon).

`openubem/outputs/06_mc_t22_diurnal_curve_nyc_centre.png` — UTCI at three points (domain centre,
the single sunniest cell, the single most-shaded cell) across all 168 h: seven clean day/night
cycles, the sunniest and centre points tracking almost identically (both largely unshaded), the
shaded point running up to ~10 °C cooler at midday peaks and converging with the others at night —
the expected physical signature of shade mattering most when the sun is up and least once it sets.

---

## 6. Higher-tier run — what is and is not usable

- **`vegetation_tier="osm"` with 185 real OSM green-space polygons ran successfully** (the code
  path executed, canopy transmission was applied per-hour via Beer–Lambert through real park/
  garden/wood/scrub geometry) — **but `domain.py::build_vegetation`'s `tier="osm"` branch tags
  `vegetation_source="osm_synthetic"` unconditionally, regardless of whether real data was
  supplied** — a pre-existing labelling imprecision in already-shipped T09 code (not part of this
  session's file list, not touched), flagged here rather than silently repeated: this run's
  manifest literally says "osm_synthetic" even though the canopy came from a real, live OSM fetch.
  Worth a future T09 follow-up; not actioned in this arc per scope.
- **`wind_tier="macdonald"` is not usable** — see §4/E-UTCI-07.
- Runtime: **989.5 s (~16.5 min)**, output size **767.1 MB** (the wind-field raster alone is 53.7
  MB here vs. 3.8 MB in the default run — a spatially-varying macdonald field compresses far
  worse than cost730's spatially-uniform one, independent of the defect, a real and expected
  artifact of the tier actually doing spatial work).
- UTCI/exposure numbers from this run (peak max 44.637 °C — **bit-identical to the default run's
  own peak max**, mean-mean 28.68 °C, CTSI mean 779.3 / max 941.4 °C·h) did not blow up
  numerically at the domain-wide summary-statistic level, and the identical peak value across
  both runs is itself consistent with the domain's single hottest cell sitting in open ground
  unaffected by either tier change (no nearby buildings for macdonald to reduce wind, no nearby
  canopy for osm vegetation to shade it). **But the domain-wide summary statistics hide a real,
  spatially-concentrated error** — see §4's direct-comparison figure
  (`06_mc_t22_tier_comparison_utci_mean.png`) and the quantified deltas there. Do not read "the
  summary numbers look similar" as "the macdonald run is fine, just its wind field export is
  cosmetically wrong" — it is not.

---

## 7. Known limitations (feeding CP-4 §7 item 4)

- 🟡 **UPDATED 2026-07-24, see §9:** `wind_tier="macdonald"` no longer produces physically
  impossible values — E-UTCI-07 and E-UTCI-08 are both resolved and independently re-verified
  (zero `0<=v_1p1<=v10` violations domain-wide). It **safely degrades to `cost730`** for 31.56% of
  this domain's cell-hours (real mid/high-rise stock exceeds its intended low-rise regime) and is
  **validated as safely-degrading, not as accurate**, on domains like `nyc_centre` — no independent
  ground truth (CFD/field/wind-tunnel) exists to validate the remaining ~68% against. This entry is
  left in place rather than deleted, per this document's own "a silent correction is
  indistinguishable from a mistake" rule (§8) — the original finding below (§4/§6) is what §9's fix
  responds to.
- `vegetation_tier="none"` is this arc's honest default — no LiDAR canopy data exists for any of
  the 12 validated cells (Q-02, still open).
- `wall_temp_tier="empirical"` uses a single representative south-facing wall azimuth (180°),
  spatially uniform — the Tier-2 EnergyPlus coupling exists (T13/`resim.py`) and is wired into
  `run_step6` (T18) but was not exercised live in T22 (not named in T22's own scope).
- Flat DEM assumption (`dem_source="assumed_flat"`) — no user DEM supplied for `nyc_centre`.
- Nighttime `Tmrt` runs well below `Ta` (E-UTCI-06, documented, closed) — a property of this
  entire model class (SOLWEIG/RayMan/ENVI-met), not specific to this port.
- No population raster anywhere in the project — PHEH is reported as honest area-hours
  (`area_hours_extreme_heat_m2h`), never a fabricated person-hours figure.
- 121/738 buildings (16.4%) excluded from the DSM for missing OSM height — an honest, flagged gap.
- No measured outdoor-comfort data exists for any validated cell — every number above is an
  internal-consistency/behavioural result, never an accuracy-vs-measurement claim (Q-05).

---

## 8. Addendum — post-fix macdonald re-run (E-UTCI-07 fix verified; a second defect, E-UTCI-08, found)

After the manager adjudicated E-UTCI-07 (fall back to `cost730` whenever the code's own existing
`10.0 - d <= ped_height_m` floor condition would engage), the fix was verified in place and
`nyc_centre`'s macdonald run was repeated (`openubem/outputs/stage6/nyc_centre_tier2wind_osm_postfix/`,
396.8 s, SVF cache reused from the domain-identical prior run):

| | Pre-fix (§4/§6 above) | Post-fix |
|---|---|---|
| `wind_clamp_cell_hours` | 64,189,257 (43.4%) | **42,074,145 (28.4%)** — now close to the clean default run's 39,634,560 (26.8%) |
| `wind_macdonald_domain_invalid_cell_hours` | (counter did not exist pre-fix) | **43,203,216 / 147,969,024 = 29.2%** of all cells — matches the adjudication's own prediction |
| Cell-hours with `\|v\| > 50 m/s` | 241,755 (0.2135%) | **64,923 (0.0573%)** — 73% fewer |
| Max `\|v_1p1\|` | 834,439 m/s | **142,357 m/s** — 83% lower peak |

**The fix works as adjudicated and substantially improves the field — but does not eliminate the
defect.** A new test T15's own updated "How to test" required (`0 <= v_1p1 <= v10` for every
macdonald output) still fails, at cells the fix's own trigger does not flag. Root-caused to a
**second, structurally broader route to the same near-zero-denominator coincidence**
(`log_10_over_z0 = ln((10-d)/z0)` can collapse toward zero whenever `(10-d)` happens to land close
to `z0`, not only when `d` itself approaches 10 m). Confirmed on this same real domain: 1.22–1.23%
of all cells hit it diagnostically; the post-fix re-run's own raster independently confirms
64,923 cell-hours / 142,357 m/s max, above. Full write-up, root cause, and candidate resolutions:
plan §10 **E-UTCI-08** (OPEN-BLOCKED).

**Consequence for this document's own §4/§6 above:** unchanged and still accurate as a description
of the *pre-fix* run and the *original* defect it found — left as-is rather than rewritten, per
this arc's own "a silent correction is indistinguishable from a mistake" discipline (T23's own
"How"). This addendum is the up-to-date status: `wind_tier="macdonald"` remains **not** usable
as "sane domain-wide" after the E-UTCI-07 fix, for the *additional*, distinct reason in E-UTCI-08.
CP-4 is not signed.

---

## 9. Final status — E-UTCI-08 fix verified, macdonald tier genuinely sane domain-wide

The manager adjudicated E-UTCI-08 (§8 above) with a postcondition sanity check: after computing
`v_1p1` (including the E-UTCI-07 domain-invalid substitution), discard it and fall back to
`cost730` whenever it violates the physically-necessary bound `0 <= v_1p1 <= v10`, regardless of
which numerical route produced the violation. Implemented in `wind.py`, unit-tested, and then
`nyc_centre_tier2wind_osm_postfix/` was regenerated **fully fresh** (macdonald wind + osm
vegetation, 168 h, 412.0 s) — a full re-run, not a patch of the four files an unrelated operational
incident had truncated to 0 bytes (E-UTCI-08's own resolution text; no scientific conclusion in
this document ever depended on reading those truncated files, and this fresh run supersedes them
entirely).

**Both manifest counters, reported plainly as instructed — how much of this domain the macdonald
tier can actually serve directly:**

| Counter | Cell-hours | % of all 147,969,024 cell-hours |
|---|---|---|
| `wind_clamp_cell_hours` | 39,761,116 | 26.87% — now within 0.32% of the clean default (`cost730`) run's 39,634,560 (26.8%), itself corroborating evidence the field is behaving sanely again |
| `wind_macdonald_domain_invalid_cell_hours` (E-UTCI-07 trigger) | 43,203,216 | 29.20% |
| `wind_macdonald_numerical_anomaly_cell_hours` (E-UTCI-08 trigger, NEW) | 3,500,400 | 2.37% of all cell-hours; 3.34% of the 104,765,808 cell-hours where the in-canopy formula was actually evaluated |
| Combined (either fallback engaged) | 46,703,616 | 31.56% |

Read honestly: on this real, dense, mid/high-rise domain (mean building height 41.9 m), the
macdonald in-canopy formula is genuinely inapplicable for 29.2% of all cell-hours (E-UTCI-07's own
domain-validity boundary), and a further 3.3% of the *remaining, domain-valid* cell-hours hit a
distinct numerical near-singularity the E-UTCI-08 postcondition check catches. **Just under a third
of this domain's cell-hours run on the `cost730` open-terrain fallback rather than the true
in-canopy formula.** That is not a residual defect — it is what "safely degrading outside its
intended regime" concretely means for a real high-rise domain, and it is reported here as useful
diagnostic information, not smoothed over.

**Independent domain-wide verification, not just the counters.** The exact per-hour `v10` sequence
this run used was re-derived (same resolved EPW, same `select_window(mode="hottest_week")` call)
and every band of the fresh `06_mc_wind_1p1m_hourly.tif` was checked cell-by-cell against
`0 <= v_1p1 <= v10`, outside building interiors: **113,250,144 valid cell-hours checked, 0
violations, maximum violation margin 0.0 m/s.** This is the literal bound the E-UTCI-08
adjudication required to hold "domain-wide," verified directly against the on-disk artifact.

**What this means for how `macdonald` should be described, going forward (per the manager's own
instruction, and now supported by direct evidence rather than a projection):** `macdonald` is
**validated to safely degrade to the `cost730` open-terrain profile** on domains outside its
intended regime — real mid/high-rise stock like `nyc_centre` — never producing a physically
impossible value, with the fallback rate honestly reported via two distinct manifest counters. It
is **not** validated as *accurate* on such domains: 31.56% of its cell-hours are not really running
the in-canopy formula at all, and the remaining ~68% have not been checked against any independent
ground truth (no CFD/wind-tunnel/field reference exists in this project, §12). Both fixes changed
only `wind.py` and its own tests — `cost730`, and every CP-1 through CP-3 gate, remain untouched
and valid throughout.

**CP-4 verdict: this closes the last blocker.** See the plan doc's own CP-4 checkpoint entry (§9)
for the full self-signing evidence bundle.

---

*T22 write-up. Manager-facing evidence for CP-4 — see the plan doc §7 CP-4 box, §10 E-UTCI-07 for
the original finding this run surfaced, §10 E-UTCI-08 for the second, distinct defect the first fix
left open, and §9 above for the final, clean re-verification that resolved it.*
