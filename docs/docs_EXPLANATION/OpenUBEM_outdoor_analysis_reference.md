# OpenUBEM — Outdoor Analysis Reference

**What this document is:** the single place to look up **everything OpenUBEM measures, derives, or
reports about the outdoor environment** — the space *between* the buildings rather than inside them.
It is a quick-lookup registry, not a design spec: definitions, units, measurement heights, valid
ranges, data sources, and current implementation status, in tables you can scan.

**Why it exists separately from [`OpenUBEM_fundamentals.md`](OpenUBEM_fundamentals.md):** the
fundamentals document explains the building-energy pipeline (Stages 1–5). Outdoor analysis is a
second, orthogonal perspective that will grow over time — outdoor thermal comfort first, then
whatever comes next. Keeping it in one registry means you never have to hunt across plan docs to
find "what unit is that in?" or "at what height is that measured?".

> **Status legend used throughout.**
> ✅ **implemented & validated** · 🔨 **in development** · 📋 **planned — plan doc written** ·
> 💡 **candidate — no plan doc yet, nothing specified** · ⏸ **deferred — deliberately not built**

**Current contents at a glance:**

| Analysis | Metric | Status | Where |
|---|---|---|---|
| Outdoor thermal comfort | **UTCI** — Universal Thermal Climate Index | ✅ built & live-run-verified (both wind tiers — `macdonald` safely degrades outside its regime, see caveat) | §2 |
| Microclimate driver fields | `Ta`, `RH`/`e`, `v`, `Tmrt` | ✅ built & live-run-verified (`cost730` live-verified accurate; `macdonald` live-verified to safely degrade to `cost730`, not accurate, on real mid/high-rise domains — §3.1) | §3 |
| Radiative geometry | Sky View Factor, shadow, horizon angles | ✅ built & live-run-verified | §3 |
| Surface temperatures | ground `T_grd`, facade `T_wall` | ✅ built (Tier 1, empirical) & live-run-verified · 🔨 Tier 2 (real EnergyPlus) built, wired, not yet live-run-verified | §3 |
| Population heat exposure | PHEH, CTSI | ✅ built & live-run-verified (area-hours only — no population raster) | §4 |
| Heat mitigation scenarios | ΔUTCI per intervention | ✅ built (5 scenarios, T24 2026-07-24) — sign-correct; 3 of 5 undershoot the literature's magnitude for documented model-scope reasons, see §5 | §5 |
| Everything else | PET, SET*, WBGT, wind comfort, UHI intensity, … | 💡 candidates | §6 |

> 🟡 **Known limitation, fixed 2026-07-24 (was a defect through two rounds, E-UTCI-07/E-UTCI-08,
> now resolved and independently re-verified):** the `macdonald` in-canopy wind tier originally
> produced physically impossible wind speeds (up to ~400,000 m/s) on real building heights above
> ~10-15 m — found on the live `nyc_centre` run 2026-07-24, root-caused, fixed in two adjudicated
> rounds (a domain-validity fallback, then a postcondition sanity check closing a second,
> structurally distinct numerical route to the same failure). **Re-verified directly against the
> on-disk raster: 0 bound violations across 113,250,144 valid cell-hours checked, on the real
> `nyc_centre` domain.** What this actually means for use: on this domain, `macdonald` falls back
> to the `cost730` open-terrain profile for **31.56%** of cell-hours (29.20% genuinely outside its
> physical regime, a further 2.37% caught by the numerical safety net) — it is **validated to
> safely degrade**, never to produce an impossible value, but **not validated as accurate** for the
> ~68% of cell-hours where it does run the in-canopy formula (no independent ground truth exists to
> check against). Full detail: `docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md`
> §10 E-UTCI-07/E-UTCI-08 and `OpenUBEM_results_UTCI_microclimate.md` §9. The default `cost730`
> wind tier was unaffected throughout and remains the tier every other number below assumes unless
> stated otherwise.

---

## 1. The one-paragraph orientation

OpenUBEM's Stages 1–5 estimate how much **energy** each building in a neighbourhood uses. Outdoor
analysis asks the complementary question: **what is the environment those buildings create, at
street level, for the people standing in it?** The two are physically coupled in both directions —
buildings shade the street and reject heat into it, and the street's air temperature drives the
buildings' cooling loads — but OpenUBEM couples them **one way only** (buildings → outdoors). The
outdoor layer reads the building simulation's results; it never feeds back into it.

Everything in this registry is evaluated at **pedestrian height, 1.1 m above ground** unless the
table says otherwise, on a **regular horizontal raster grid** covering the neighbourhood, at hourly
resolution over a selected analysis window.

---

## 2. Outdoor thermal comfort — UTCI

**Status:** ✅ built, tested (138 unit tests), and live-run-verified on real geometry
(`nyc_centre`, 738 buildings, 2026-07-24) at the default tier set (`vegetation=none`,
`wall_temp=empirical`, `wind=cost730`). ✅ the `wind=macdonald` and `vegetation=osm` higher tiers
also ran live and are now promoted, with a stated caveat: `macdonald` is re-verified
(2026-07-24, E-UTCI-07/E-UTCI-08 both resolved) to safely degrade to `cost730` — zero
physically-impossible values domain-wide — but not verified as accurate on real mid/high-rise
domains, where it substitutes the `cost730` fallback for 31.56% of cell-hours (see the banner
above). Real measured ranges are in §2.6/§3.1; the full write-up is
[`OpenUBEM_results_UTCI_microclimate.md`](../docs_DONE/OUTDOOR/UTCI/results/OpenUBEM_results_UTCI_microclimate.md).
**Product status:** **separate analysis product — NOT a headline OpenUBEM output** (user decision,
2026-07-23). UTCI does not appear in `05_results.*` or the neighbourhood summary, Stage 6 does not
run as part of a standard pipeline run, and the 3D viewer still colours buildings by energy. See
§2.9 for the reason: **UTCI is not validated against measured data, and EUI is.**
**Plan doc:** [`docs/docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md`](../docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md)
**Research corpus:** `docs/docs_DONE/OUTDOOR/UTCI/DeepResearches/` (U01–U06) — ⚠️ see §2.8 before using it.

### 2.1 What UTCI is

The **Universal Thermal Climate Index** is an *equivalent temperature*: the air temperature of a
defined reference environment that would impose the **same physiological strain** on a standardised
person as the actual, complex outdoor environment does. It answers "how hot or cold does it *feel*",
in °C, on a scale a non-specialist can read.

It is derived from the **UTCI-Fiala multi-node model of human thermoregulation** (187 tissue nodes,
15 body segments), which simulates sweating, shivering, vasodilation, vasoconstriction, respiratory
heat loss, and wind-driven clothing ventilation. Because running that model takes 1–5 seconds per
point, operational use relies on a **6th-degree polynomial approximation** fitted to ~200,000
steady-state solutions of it.

| Property | Value |
|---|---|
| Unit | °C (equivalent temperature) |
| Inputs | exactly four: `Ta`, `Tmrt`, wind speed, water-vapour pressure |
| Approximation error vs full Fiala model | **RMSE 0.11 °C**, max abs 0.29 °C, R² 0.9995 |
| For context | human inter-individual comfort variation is **±1.5 °C** — the approximation error is negligible beside it |
| Evaluation cost | < 1 µs per point, vectorised |

### 2.2 The reference environment and the standardised person

UTCI values only mean something against the reference conditions the index is defined by. These are
**fixed by the standard** — they are not OpenUBEM settings and cannot be changed.

| Assumption | Value |
|---|---|
| Metabolic rate | 135 W/m² (**2.3 MET**) — walking at 4 km/h on level ground |
| Body | 73.5 kg, DuBois surface area 1.85 m² |
| Reference wind | 0.5 m/s at 1.1 m |
| Reference radiant condition | `Tmrt = Ta` (radiative equilibrium) |
| Reference humidity | 50 % RH below 29 °C; 20 hPa vapour pressure above |
| Clothing | **self-adaptive, 0.3–2.6 clo** as a function of air temperature, plus wind and walking-motion corrections |

The self-adaptive clothing model is the main reason UTCI outperforms older indices outdoors: PET
assumes a fixed 0.9 clo (a business suit, in July), and PMV assumes indoor air velocities below
0.2 m/s. Both break down in real streets.

### 2.3 🌡️ The stress scale — the lookup table

**This is the 10-class official scale.** Note it covers cold as well as heat; the widely-circulated
5-class heat-only graphic is a public-communication simplification and is **not** what OpenUBEM
implements.

| UTCI (°C) | Stress category | Colour | Hex |
|---|---|---|---|
| **> +46** | Extreme heat stress | deep maroon | `#800000` |
| **+38 … +46** | Very strong heat stress | bright red | `#FF0000` |
| **+32 … +38** | Strong heat stress | orange | `#FF7F00` |
| **+26 … +32** | Moderate heat stress | yellow | `#FFFF00` |
| **+9 … +26** | **No thermal stress** (comfort) | green | `#00FF00` |
| **0 … +9** | Slight cold stress | cyan | `#00FFFF` |
| **−13 … 0** | Moderate cold stress | medium blue | `#007FFF` |
| **−27 … −13** | Strong cold stress | dark blue | `#0000FF` |
| **−40 … −27** | Very strong cold stress | violet | `#8B00FF` |
| **< −40** | Extreme cold stress | indigo | `#4B0082` |

Bounds are half-open `[min, max)`: a cell at exactly 26.0 °C is *Moderate heat stress*.

### 2.4 Municipal risk tiers

A 4-tier presentation layer over the 10 physiological classes, for planning audiences. It is a
**view**, never a replacement for the classes above.

| Tier | UTCI | Typical municipal action |
|---|---|---|
| Comfort | +9 … +26 | Baseline. No intervention. |
| Caution / mitigation alert | +26 … +32 | Prioritise urban forestry, cool roofs, shaded pedestrian corridors. |
| High vulnerability | +32 … +38 | Public health warnings; outdoor-labour shade breaks; hydration stations. |
| Emergency | > +38 | Cooling centres opened; vulnerable-population outreach. |

### 2.5 Validity domain — inputs outside this box are clamped

The polynomial **diverges** outside its fitted box, producing values above 100 °C or below −150 °C.
OpenUBEM clamps every input and records which clamp fired, per cell, in a bitmask raster.

| Input | Min | Max | Clamp flag |
|---|---|---|---|
| Air temperature `Ta` | −50 °C | +50 °C | `0x01` |
| Radiant offset `Tmrt − Ta` | −30 °C | +70 °C | `0x02` |
| Wind speed `va` (**at 10 m**) | 0.5 m/s | 17.0 m/s | `0x04` |
| Water-vapour pressure `e` | 0 kPa | 5 kPa | `0x08` |

> The **wind clamp fires constantly** in dense urban canyons, where modelled air speed routinely
> falls below 0.5 m/s. This is expected, not a defect: the standard clamps to 0.5 m/s because a
> *walking* person always experiences at least that much relative air motion. It is recorded rather
> than swallowed so that a reader can tell how much of a map sat on the floor of the domain.

### 2.6 What actually drives the spatial pattern

Ranked by influence on the **spatial** variation of UTCI across a neighbourhood — which is not the
same ranking as influence on its absolute value.

| Rank | Driver | Sensitivity | Why it ranks there |
|---|---|---|---|
| **1** | **Mean radiant temperature `Tmrt`** | ≈ **+0.31 °C UTCI per +1 °C Tmrt** | Varies **20–30 °C** across one block (sunlit pavement ~65 °C vs deep canopy shade ~40 °C). Utterly dominant. |
| 2 | Air temperature `Ta` | ≈ +1.06 °C per +1 °C | Large *sensitivity*, but turbulent mixing keeps its spatial range to **0.5–1.5 °C**. |
| 3 | Wind speed | ≈ −2 °C per +1 m/s (non-linear) | Strong convective cooling; highly variable behind and between buildings. |
| 4 | Relative humidity | ≈ +0.1 °C per +1 % RH | Suppresses evaporative cooling. Nearly uniform across a neighbourhood. |

**The practical consequence:** shade is the lever. Stepping from sun into shade drops `Tmrt` by
~20 °C and UTCI by **6–7 °C** — enough to cross two stress categories — while doing almost nothing
to air temperature. Mitigation that cools the air is worth far less than mitigation that blocks sun.

### 2.7 What OpenUBEM produces — confirmed by the `nyc_centre` live run

| Artifact | Contents | Measured (nyc_centre, default tiers, 168 h) |
|---|---|---|
| `06_mc_utci_hourly.tif` | UTCI per cell per hour, one band per hour, float32 GeoTIFF | 330.9 MB |
| `06_mc_utci_peak.tif` / `06_mc_utci_mean.tif` | window aggregates | peak 34.8–44.6 °C, mean 25.1–29.2 °C |
| `06_mc_utci_peak_class.tif` / `06_mc_utci_mean_class.tif` | 10-class companion, GDAL colour table embedded | — |
| `06_mc_flags_hourly.tif` | per-cell clamp bitmask (§2.5), extended with the wind- and Ta-tier clamp bits | — |
| `06_mc_summary.gpkg` | per-building outdoor-comfort attributes joined onto `05_results.gpkg` (read-only) | 738 rows |
| `06_mc_exposure_metrics.json` | PHEH / CTSI (§4) | see §4 |
| `06_mc_manifest.parquet` | every config value, tier, EPW hash/resolution path, and flag count used | — |

Total output for this one cell/window/resolution combination: **715 MB** (default tiers). This is
the real cost the analysis-window scoping decision (not running 8760 h by default) exists to
bound — full engineering detail and both live runs' complete numbers are in
[`OpenUBEM_results_UTCI_microclimate.md`](../docs_DONE/OUTDOOR/UTCI/results/OpenUBEM_results_UTCI_microclimate.md).
**Runtime:** ~15 minutes end to end for this domain (896×983 cells at 2 m resolution), of which
the one-time sky-view-factor computation is the dominant cost (~9 minutes), paid once per domain,
never per hour.

The building-joined GeoPackage is the one that makes this a *UBEM* product rather than a standalone
microclimate study: it lets you ask **"which buildings sit in the worst outdoor heat?"** and
cross-reference that against their energy use, archetype, and vintage.

### 2.8 ⚠️ Known traps when reading the UTCI literature and our research corpus

Four things are easy to get wrong and fail **silently** — no crash, no obviously wrong map. They are
recorded here because they bite readers, not just implementers.

| Trap | The correct fact |
|---|---|
| **Wind height** | The polynomial's wind argument is at **10 m**, not 1.1 m. Feeding it a pedestrian-level value makes every result several °C too warm. OpenUBEM computes the 1.1 m field for display and converts back (`÷ 0.680`) before evaluating. |
| **Vapour-pressure unit** | The official routine takes **hPa**. A kPa/hPa slip is a silent factor of 10. |
| **Radiative weighting factors** | For a standing person: **0.22** × 4 vertical planes, **0.06** × 2 horizontal. They must sum to exactly 1.00. |
| **Our own research corpus** | `docs/docs_DONE/OUTDOOR/UTCI/DeepResearches/` (U01–U06) is a **research input, not a specification.** A manager audit found **7 load-bearing defects**, including a *fabricated* UTCI polynomial (7 hand-written terms standing in for the real 210 coefficients). The full list and corrections are in §4 of the plan doc and in `docs/docs_DONE/OUTDOOR/UTCI/implementation/README.md`. |

### 2.9 Accuracy expectations, stated honestly

- The **polynomial** is essentially exact (0.11 °C RMSE) — it is a transcription problem, not a
  physics problem, and it is gated as such.
- The **`Tmrt` field** is where real error lives. Published validation of comparable 2.5D radiation
  models gives **RMSE 2.5–4.2 °C, R² > 0.92** against field radiometers under clear sky. That is the
  realistic bar.
- The single largest uncertainty is **ground surface temperature**: unshaded asphalt runs +25 to
  +32 °C above air temperature, irrigated turf only +2 to +5 °C. Failing to resolve ground material
  causes `Tmrt` errors up to **±6 °C**.
- **There is no measured outdoor-comfort data for our validated cities.** Every gate on this arc is
  internal-consistency or behavioural, never accuracy-vs-measurement. Do not report a UTCI map as
  "validated against measurement" — it is not, and it will not be without a field campaign.

> **This is why UTCI is kept a separate product (user decision, 2026-07-23).** Building EUI is
> validated against measured data — NYC Local Law 84, LA EBEWE, national CBECS — and that evidence
> underwrites the project's ±9 % claim. UTCI has no such anchor. Placing it in the same results
> table, with the same apparent authority, would lend it credibility it has not earned, and a
> hurried reader would not tell the two apart. Promotion to a headline output stays available as a
> **future** decision, on new evidence: after a measurement campaign, or for cells with a
> measurement anchor. It is not a re-litigation of this one.

### 2.10 Why UTCI and not one of the older indices

| Index | Why it fails outdoors |
|---|---|
| **PMV / PPD** (ISO 7730) | Built by Fanger for steady-state indoor HVAC. Assumes fixed clothing and air velocity < 0.2 m/s. Breaks down entirely under solar load and real wind. |
| **PET** | Two-node model with **fixed 0.9 clo** and 80 W activity. Overestimates summer heat strain (it dresses everyone in a suit) and understates extreme cold. |
| **Heat Index** | Hot/humid only. **Ignores solar radiation and wind entirely** — the two things that vary most across a street. |
| **Wind Chill** | Cold/windy only. Ignores radiative gain. |
| **UTCI** | One continuous scale, all climates, all seasons; full active thermoregulation; adaptive clothing; accounts for all four drivers. |

---

## 3. Microclimate driver fields and derived geometry

**Status:** ✅ built and live-run-verified — Stage 6. These are the intermediate quantities
computed on the way to UTCI, and each is exported in its own right because each is independently
useful.

### 3.1 The four UTCI driver fields

| Field | Symbol | Unit | Height | Source in OpenUBEM | Status |
|---|---|---|---|---|---|
| Air temperature | `Ta` | °C | 1.1 m | EPW dry-bulb (field 7), spatially uniform by default; optional bounded canyon-UHI and HVAC-rejection offsets | ✅ Tier 0 live-verified; 🔨 Tier 1 (offset) built + unit-tested, not exercised live |
| Relative humidity / vapour pressure | `RH` / `e` | % / kPa | 1.1 m | EPW relative humidity (field 9) → Buck (1981) saturation vapour pressure | ✅ live-verified |
| Wind speed | `v` | m/s | **1.1 m** (exported) and **10 m equivalent** (fed to UTCI) | EPW wind speed at 10 m (field 21), downscaled by log profile or Macdonald morphometric canopy model | ✅ `cost730` (log profile) live-verified, accurate · ✅ `macdonald` (morphometric canopy) live-verified to **safely degrade** to `cost730` (0 physically-impossible values across 113,250,144 checked cell-hours on real `nyc_centre`, after two adjudicated fixes, E-UTCI-07/E-UTCI-08) — **not** verified as accurate: it substitutes the `cost730` fallback for 31.56% of cell-hours on this real mid/high-rise domain, outside its intended low-rise regime. See the banner at the top of this document and plan §10 E-UTCI-07/E-UTCI-08. |
| Mean radiant temperature | `Tmrt` | °C | 1.1 m | Computed — 6-directional shortwave + longwave flux balance | ✅ live-verified |

**Typical urban summer ranges**, for sanity-checking a map (from published field/simulation studies,
not from our runs): `Ta` 34.5–35.2 °C · `RH` 45–50 % · `v` 0.58–3.0 m/s · `Tmrt` **40–65 °C** ·
resulting UTCI 33 – >44 °C. Note how narrow the first three are and how wide `Tmrt` is — §2.6 again.

**Measured on `nyc_centre`** (738 buildings, 168 h hottest-week window, default tiers,
2026-07-24): `Ta` 20.0–33.9 °C (real EPW dry-bulb, day/night cycle over the week) · `v(1.1m)`
0.0–3.88 m/s, mean 1.12 m/s (`cost730` tier; genuinely calm hours — 0.0 m/s exactly — occur
repeatedly in this resolved TMYx file, verified against the raw EPW rows, not a bug) ·
`Tmrt` 7.13–69.76 °C. The `Tmrt` floor is markedly colder than `Ta`'s own floor (a ~13 °C gap) —
this is the already-documented nighttime under-prediction this model family carries (§3.2, and
plan §10 E-UTCI-06), showing up as expected in real data, not a new defect. Peak UTCI reached
44.6 °C ("Very strong heat stress") at the hottest hour; the week-mean UTCI sat in "Moderate heat
stress" (26-32 °C) across 98.2% of the domain's open area. Differences from the published ranges
above are expected (different site, different week) and are explained, not tuned away, in the
full write-up.

### 3.2 Mean radiant temperature — the composition

`Tmrt` synthesises every radiant flux reaching a human body into one equivalent blackbody
temperature:

```
Tmrt = ( S_str / (ε_p · σ) )^0.25 − 273.15        ε_p = 0.97, σ = 5.670374e-8 W/(m²·K⁴)
S_str = 0.70 · K_abs  +  0.97 · L_abs             (shortwave absorptivity, longwave absorptivity)
```

| Flux component | Symbol | What drives it |
|---|---|---|
| Direct beam solar | `K_dir` | EPW direct normal irradiance, gated by building + tree shadow, weighted by the projected-area factor of a standing person |
| Diffuse sky solar | `K_diff` | EPW diffuse horizontal × sky view factor |
| Reflected solar | `K_refl` | Ground and facade **albedo** — the term responsible for the cool-pavement paradox (§5) |
| Sky longwave | `L_sky` | EPW horizontal infrared, or Prata parameterisation with cloud correction, × sky view factor |
| Ground longwave | `L_grd` | Ground surface temperature `T_grd` (§3.4) |
| Facade longwave | `L_wall` | **EnergyPlus exterior surface temperature `T_wall`** (§3.4) |
| Canopy longwave | `L_tree` | Leaf temperature ≈ `Ta` ± transpiration offset, ε = 0.98 |

### 3.3 Radiative geometry (static — computed once per site)

| Quantity | Symbol | Unit | Meaning |
|---|---|---|---|
| Sky view factor | `Ψsky` | 0–1 | Fraction of the sky hemisphere visible from a point. 1.0 = open field, → 0 in a deep canyon. Gates both diffuse solar and sky longwave. |
| Horizon angles | `γ(φ)` | ° | Maximum obstacle elevation in each of 32 azimuths. Reused by every hour's shadow computation. |
| Building shadow | `S_bldg` | {0, 1} | Binary — a wall either blocks the sun or it does not. |
| Vegetation transmission | `τ_veg` | 0–1 | Fractional, via Beer–Lambert through the crown. Summer deciduous 0.10–0.30; winter leafless 0.40–0.70; coniferous 0.05–0.15. |
| Digital surface model | `DSM` | m | Ground elevation + building heights, rasterised. |
| Canopy surface model | `CDSM` / `TDSM` | m | Tree crown top and trunk-zone base heights. The trunk zone matters: low sun passes *under* a canopy. |

Analytic cross-check for a uniform street canyon of height `H` and width `W`, observer at height
`z` above the canyon floor (the platform computes at pedestrian height, `z = 1.1 m` by default):
`Ψsky = 1 / √(1 + (2(H−z)/W)²)` (Oke 1981, extended to an elevated observer). Corrected
2026-07-23 — see the implementation plan's E-UTCI-01 for why the earlier `√(1+(2H/W)²) − 2H/W`
form was wrong (a different configuration factor, not this one), and E-UTCI-02 for the
pedestrian-height correction to the `z=0` floor-level special case. **Status: ✅ built and
live-run-verified** — measured mean SVF outside building footprints on `nyc_centre` (200 m
buffer around 738 real buildings): **0.873**.

#### 3.3.1 `height_m` provenance feeding the DSM — the multi-source fusion path

**Status: ✅ built** (E-UTCI-09 height-backfill sub-plan,
`docs/docs_DONE/OUTDOOR/UTCI/implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md`, 2026-07-25) —
**materially fixed, with a documented residual, not fully closed.**

The DSM row above (`Ground elevation + building heights, rasterised`) depends entirely on
`height_m` being populated. Four of the twelve validated cluster cells had `height_m` missing for
84.5–100 % of their buildings, which collapsed the DSM to a flat plane and drove `svf_mean` to
exactly **1.0000** — the open-field signature, not a real property of those tracts (`nyc_suburban`,
`nyc_rural`, `austin_rural` 100 % missing; `austin_centre` 84.5 %). The existing spatial imputer
(`knn_fill`) could not repair this: every donor in a 100 %-missing cell is missing the same column,
so it filled **0** rows at every search radius up to 1000 m.

**The fix routes `height_m` through OpenUBEM's multi-source fusion tier**
(`openubem/semantic/fusion.py`, `openubem/semantic/imputation.py::_fusion_tier`) — first-hit-wins
across `overture` (primary, backed by a one-off cached Overture Maps pull over each affected
tract's bounding box), `lidar`, and `assessor` (both wired but unconfigured). Every fused value
carries a `FUSED_OVERTURE_HIGH`/`_MED` provenance token and passes a **minimum-height sanity floor**
(`_MIN_HEIGHT_FLOOR_M = 2.1 m`, IRC/IBC R305.1's minimum habitable-storey height) before landing —
a fused value below the floor is discarded, not shipped, because the raw external source can
contain physically absurd heights (a 0.216 m "building" was found in one cell's slice). Rows fusion
cannot fill fall through to the existing spatial tier, which can now donate from **real,
in-cell neighbours** because post-fusion residual missingness drops below the platform's 60 % MNAR
guard in every cell.

**Result — `svf_mean` before/after** (full comparison:
`openubem/outputs/comparisons/t11_e_utci_09_before_after_comparison.csv` and
`t11_e_utci_09_svf_before_after.png`):

| cell | `svf_mean` before | `svf_mean` after | `n_excluded_no_height` before → after |
|---|---|---|---|
| `nyc_suburban` | 1.0000 | **0.9619** | 1589 → 15 |
| `nyc_rural` | 1.0000 | **0.9972** | 198 → 72 |
| `austin_centre` | 0.9474 | **0.8426** | 349 → 11 |
| `austin_rural` | 1.0000 | **0.9935** | 245 → 47 |

All four cells leave the 1.0000 open-field signature and land at values consistent with their real
fabric (e.g. `austin_centre`'s post-fix max filled height, 216 m, matches downtown Austin's real
high-rises; the three lower-density cells fill in the 2–9 m low-rise range). The other 8 validated
cells are confirmed byte-identical with fusion on vs. off — 0 previously-observed `height_m` values
were overwritten anywhere.

**The documented residual — not a full close.** Fusion plus the spatial tier still leave rows
`NaN` (excluded from the DSM, same as any genuinely-missing height): **15** in `nyc_suburban`
(0.9 % of its original 1589-row gap), **72** in `nyc_rural` (36.4 %), **11** in `austin_centre`
(3.2 %), **47** in `austin_rural` (19.2 %). The flat-open-field artefact is gone everywhere, but
rural coverage in particular stays partial — a future arc would need a denser external source (the
already-wired but unconfigured `lidar`/`assessor` fusion sources, or a lower floor with a different
provenance tier) to close the remainder. See the sub-plan's own progress log (T07/T11) and
`docs/docs_EXPLANATION/OpenUBEM_imputation_methods.md` §4.1 for the full mechanism.

### 3.4 Surface temperatures

| Quantity | Symbol | Source | Status | Notes |
|---|---|---|---|---|
| Ground surface temperature | `T_grd` | Surface energy balance solved per cell (Newton iteration on the quartic) | ✅ live-run-verified (100% Newton convergence on `nyc_centre`) | Depends on albedo, emissivity, conductivity, and latent flux from the land-cover raster. **Largest single uncertainty in the longwave balance.** |
| Facade surface temperature | `T_wall` | **Tier 2: real EnergyPlus `Surface Outside Face Temperature`.** Tier 1: empirical offset from `Ta`. | ✅ Tier 1 (empirical, single representative south-facing wall) live-run-verified · 🔨 Tier 2 built and wired into the Stage-6 orchestrator, unit-tested with mocked EnergyPlus results — **not yet exercised on a real EnergyPlus run** | This is OpenUBEM's differentiator — see below. |

> **Why `T_wall` matters, and why it is OpenUBEM's contribution here.** Every comparable 2.5D
> microclimate tool assumes facade temperature ≈ air temperature, because it has no building model.
> OpenUBEM *is* a building model. Sun-heated facades raise nearby `Tmrt` by **+5 to +15 °C**, and
> thermally massive uninsulated walls hold 45–50 °C well into the evening — which is exactly when
> nocturnal urban heat stress matters most. Feeding real EnergyPlus surface temperatures into the
> longwave balance closes a gap the peer tools structurally cannot.
>
> It is gated behind a flag because `Surface Outside Face Temperature` is emitted **per surface per
> hour**: across thousands of buildings and 8,760 hours it is a multi-terabyte trap. It is only
> valid together with a restricted analysis window.

### 3.5 Coupling direction — stated once

```
EnergyPlus building simulation  ──►  outdoor microclimate  ──►  UTCI
                                (one way, no feedback)
```

OpenUBEM does **not** do two-way coupling: the outdoor air temperature field never feeds back into
the buildings' cooling loads. Two-way coupling and CFD wind fields are deliberately out of scope
(§7). Anywhere a result depends on that feedback, it is an approximation and should be reported as
one.

---

## 4. Population heat exposure metrics

**Status:** ✅ built and live-run-verified (PHEH/CTSI) — Stage 6. These turn a raster into
something a municipality can act on.

| Metric | Definition | Unit | Use | Measured (nyc_centre, 168 h, default tiers) |
|---|---|---|---|---|
| **PHEH** — Person-Hours of Extreme Heat | `Σ_zones Σ_t Pop · Δt · 𝟙(UTCI > 46 °C)` | person·h | Absolute population exposure to hyperthermia-risk conditions | `area_hours_extreme_heat_m2h = 0.0` — the >46 °C threshold was never crossed this week (peak UTCI 44.6 °C) |
| **CTSI** — Cumulative Thermal Stress Index | `∫ max(0, UTCI − 26) dt` | °C·h | Heat-wave intensity load per parcel — a degree-hours analogue above the comfort threshold | mean 780 °C·h, max 849 °C·h across the domain (a genuinely hot NYC July week) |
| **SHVI** — Spatial Heat Vulnerability Index | weighted Z-scores of mean UTCI, vulnerable population share, and canopy deficit | — | ⏸ **not built** — requires demographic rasters OpenUBEM does not have |

> **Honesty rule on PHEH:** if no population raster is available, OpenUBEM reports **area-hours**
> (`area_hours_extreme_heat_m2h`) and names the field accordingly. It never substitutes an invented
> population density to make a person-hours number appear.
>
> **Known limitation:** static census rasters assume people stay at their registered residence
> through the 14:00–16:00 peak. Real pedestrian movement, transit waits, and outdoor labour shift
> people *into* the hottest street canyons, so static exposure figures systematically **under**-count
> peak risk. Agent-based mobility is out of scope (§7).

---

## 5. Heat mitigation scenarios

**Status:** ✅ **built** — `openubem/microclimate/scenarios.py`, Stage 6 T24, completed 2026-07-24
(CP-5 signed). Five scenarios ship: `tree_canopy`, `pv_canopy`, `cool_pavement`, `cool_roof`
(an explicit alias of `cool_pavement` — this model has no separate roof-view geometry), and
`high_albedo_facade`.

Scenarios are **domain-layer edits only** (change the albedo raster, change the canopy model) — never
physics changes. Implemented by exposing three *already-existing* physics inputs that the
orchestrator previously hardcoded; all three default to `None`, reproducing prior behaviour
byte-identically.

> ⚠️ **All five scenarios reproduce the literature's *sign*; three undershoot its *magnitude*, for
> reasons that are pre-existing model scope, not scenario-engine defects.** `tree_canopy`/`pv_canopy`
> land at ≈ −3.8 / −4.8 °C because the published figures bundle a transpirational **air-temperature**
> cooling pathway that the Tier-1 air-temperature model does not implement at all — this engine only
> ever captures the shading/`Tmrt` pathway. `high_albedo_facade` reaches only +0.05…+0.24 °C because
> the wall-reflection term was deliberately built as a secondary isotropic approximation, and
> correcting it would be a physics change to already-adjudicated code. Treat the ranges below as
> **literature expectations, not as this model's verified output**; the module's own
> `ACHIEVABLE_DELTA_UTCI_RANGE_C` records what is actually tested, per scenario, alongside them.

Expected magnitudes, from the literature, used as sanity envelopes rather than as
targets:

| Intervention | Δ`Ta` | Δ`Tmrt` | **ΔUTCI** | Verdict |
|---|---|---|---|---|
| Urban tree canopy expansion | −0.5 … −1.5 °C | **−15 … −25 °C** | **−4 … −10 °C** | The most effective lever by a wide margin |
| PV canopy / solid shade sails | −0.2 … −0.8 °C | −20 … −30 °C | **−6 … −12 °C** | Most effective per m² where trees can't go |
| Cool roofs & cool pavements | −0.5 … −2.0 °C | **+2 … +8 °C** | **−0.5 … +2.0 °C** | ⚠️ Can make pedestrians *worse off* |
| High-albedo facades | −0.2 … −0.5 °C | +5 … +12 °C | **+1 … +4 °C** | ⚠️ Actively harmful at street level |

### ⚠️ The cool-pavement paradox — the most counter-intuitive result in this document

Raising pavement albedo from 0.15 (asphalt) to 0.45 (cool coating) genuinely **cools the ground** by
12–15 °C and the **air** by 0.5–1.5 °C. It is a real urban-heat-island mitigation.

But it does so by *reflecting* the solar radiation rather than absorbing it — and an upright human
body has a view factor of ≈ 0.5 to the ground. Reflected shortwave flux hitting a pedestrian's legs
and lower torso jumps from ~80 W/m² to **> 250 W/m²**. Because the human radiant load is far more
sensitive to shortwave than to the modest air-temperature drop, `Tmrt` **rises** by 3–8 °C and
**UTCI rises by +0.5 to +2.5 °C**.

**The design directive that follows:** high-albedo pavements and facades should only be deployed
**under shade** — beneath tree canopies or shade structures, or in dense canyons where direct solar
access is already blocked. In open sun they cool the city and heat the people in it.

This is also a **model correctness test**: if an OpenUBEM run reports cool pavements as a
straightforward improvement in unshaded areas, the reflected-shortwave term is wrong.

---

## 6. Future outdoor analyses — candidate register

**Status: 💡 candidates. Nothing below is specified, planned, or implemented.** They are recorded so
that (a) nobody re-derives the shortlist from scratch, and (b) it is unambiguous that they do *not*
exist yet. **Adding any one of them requires a manager-authored plan doc first** (§8).

| Candidate | One-line definition | Why it might be worth adding | Blocker |
|---|---|---|---|
| **PET** — Physiological Equivalent Temperature | Two-node equivalent temperature, fixed 0.9 clo | Still the most-cited index in European planning literature; useful for comparability with published studies | Superseded by UTCI on the physics; only worth it for cross-study comparison |
| **SET\*** — Standard Effective Temperature | ASHRAE two-node equivalent temperature | Bridges indoor (ASHRAE 55) and outdoor comfort reporting | Low marginal value once UTCI exists |
| **WBGT** — Wet Bulb Globe Temperature | ISO 7243 occupational heat-stress index | It is what **occupational safety regulation** actually uses — outdoor labour, construction, sport | Needs globe temperature; derivable from `Tmrt` and wind |
| **Pedestrian wind comfort** (Lawson / NEN 8100) | Exceedance-probability classes of gust speed for sitting / standing / walking | The other half of outdoor comfort: UTCI covers thermal, this covers mechanical (papers blowing, doors, discomfort) | Needs a **CFD or fast wind solver** — our log/morphometric profiles cannot resolve corner vortices or downdrafts |
| **UHI intensity** | Urban-minus-rural air temperature, diurnal | Directly comparable to the urban-climate literature and to municipal targets | Needs a defensible rural reference; partially available from the `Ta` offset layer |
| **Outdoor daylight / glare** | Illuminance and glare on public space | Relevant for plaza and facade design; reuses the same shortwave geometry | Needs a photometric, not radiometric, treatment |
| **Air quality dispersion** | Pollutant concentration at street level | High policy value; couples to the same canopy flow | Needs emission inventories and a dispersion model — a much larger arc |
| **Outdoor acoustic comfort** | Street-level sound pressure | Completes the "outdoor liveability" picture | Entirely separate physics; no shared machinery |

**Deliberately excluded, not merely unbuilt** — see §7.

---

## 7. Out of scope — deliberate exclusions

Stated once so they are never quietly re-scoped in:

| Excluded | Why |
|---|---|
| **CFD wind fields** | Corner vortices, downdrafts, and recirculating canyon eddies need OpenFOAM/PALM-class tooling and HPC. Our 1D vertical profiles assume horizontal homogeneity — a stated limitation, not a hidden one. |
| **Two-way building ↔ microclimate coupling** | Highest fidelity, but a massive computational burden across thousands of buildings. Peer literature classes it as research-tier only. |
| **Agent-based pedestrian mobility** | Would fix the static-census exposure bias (§4), but is a modelling arc of its own. |
| **The full 187-node Fiala model at runtime** | 1–5 s per point vs < 1 µs for the polynomial, for 0.11 °C of accuracy that is invisible beside ±1.5 °C human variation. |
| **Sub-hourly dynamics** | Outdoor analysis inherits the platform's hourly timestep. |
| **Demographic vulnerability indices** | No demographic rasters. Better absent than fabricated. |

---

## 8. How to add a new outdoor analysis

The registry only stays useful if new entries arrive the same way. The sequence:

1. **Check §6.** If the metric is already a candidate, start from its blocker.
2. **Manager writes a plan doc** under `docs/docs_ACTIVE/<arc>/implementation/`, following the
   house structure in `CLAUDE.md` (hard rules → file layout → verified facts → numbered tasks with
   what/why/how/test → checkpoints → progress log). **Executors never write the plan.**
3. **Register the metric here first**, at status 📋, with: definition, unit, measurement height,
   valid range, data source, and — critically — **what it is not**. An entry with no stated
   limitations is an incomplete entry.
4. **Verify every constant and formula at its primary source.** The single most expensive lesson of
   the UTCI arc (§2.8) is that plausible-looking equations and coefficients in secondary material
   are often wrong in ways that fail silently. Prefer a cheap invariant that would catch it — *do the
   weights sum to 1? does the published reference case reproduce?* — and bake it into a test.
5. **Zero fitted parameters.** Same rule as the building pipeline: every numeric constant carries a
   citation or it does not enter the code. Nothing is ever tuned to make a gate pass.
6. **Update the at-a-glance table** in this document's header, and add a pointer row in
   `OpenUBEM_fundamentals.md` §10.

---

## 9. Where to go next

| You want… | Read |
|---|---|
| The building-energy pipeline (Stages 1–5) | [`OpenUBEM_fundamentals.md`](OpenUBEM_fundamentals.md) |
| The UTCI implementation plan and its 26 tasks | [`../docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md`](../docs_DONE/OUTDOOR/UTCI/implementation/PLAN_utci_microclimate_implementation.md) |
| The 7 defects in the UTCI research corpus | [`../docs_DONE/OUTDOOR/UTCI/implementation/README.md`](../docs_DONE/OUTDOOR/UTCI/implementation/README.md) |
| The underlying research (U01–U06) | `../docs_DONE/OUTDOOR/UTCI/DeepResearches/` — ⚠️ research input, not a spec |
| The reference figures | `../docs_DONE/OUTDOOR/UTCI/1784462193210.jpg` (concept + scale), `…193769.jpg` (spatial field coupling) |
| Building input parameters | [`OpenUBEM_inputs_reference.md`](OpenUBEM_inputs_reference.md) |
| Current project status | [`../PROJECT_CHECKLIST.md`](../PROJECT_CHECKLIST.md) |

---

## 10. Primary references

The literature this registry rests on. Cited here once so individual sections can stay readable.

**UTCI and thermal physiology**
- Bröde, P., et al. (2012). Deriving the operational procedure for the Universal Thermal Climate Index. *Int. J. Biometeorology*, 56(3), 481–494. [doi:10.1007/s00484-011-0454-1](https://doi.org/10.1007/s00484-011-0454-1) — **the operational polynomial**
- Fiala, D., et al. (2012). UTCI-Fiala multi-node model of human thermoregulation and thermal comfort. *Int. J. Biometeorology*, 56(3), 429–441. [doi:10.1007/s00484-011-0424-7](https://doi.org/10.1007/s00484-011-0424-7)
- Havenith, G., et al. (2012). The UTCI-clothing model. *Int. J. Biometeorology*, 56(3), 461–470. [doi:10.1007/s00484-011-0451-4](https://doi.org/10.1007/s00484-011-0451-4)
- Jendritzky, G., de Dear, R., & Havenith, G. (2012). UTCI — why another index? *Int. J. Biometeorology*, 56(3), 421–428. [doi:10.1007/s00484-011-0513-7](https://doi.org/10.1007/s00484-011-0513-7)
- Psikuta, A., et al. (2012). Validation of the UTCI-Fiala multi-node model. *Int. J. Biometeorology*, 56(3), 443–459. [doi:10.1007/s00484-011-0450-5](https://doi.org/10.1007/s00484-011-0450-5)
- ISO 7730 (2005), ISO 7933 (2004), ASHRAE Standard 55 (2020)

**Radiation, mean radiant temperature, and microclimate modelling**
- Lindberg, F., Holmer, B., & Thorsson, S. (2008). SOLWEIG 1.0 — modelling spatial variations of 3D radiant fluxes and mean radiant temperature. *Int. J. Biometeorology*, 52(7), 697–713. [doi:10.1007/s00484-008-0162-7](https://doi.org/10.1007/s00484-008-0162-7)
- Lindberg, F., et al. (2018). UMEP: an integrated tool for urban climatology applications. *Environmental Modelling & Software*, 99, 70–87. [doi:10.1016/j.envsoft.2017.09.020](https://doi.org/10.1016/j.envsoft.2017.09.020)
- Matzarakis, A., Rutz, F., & Mayer, H. (2007). Modelling radiation fluxes — the RayMan model. *Int. J. Biometeorology*, 51(4), 323–334. [doi:10.1007/s00484-006-0061-8](https://doi.org/10.1007/s00484-006-0061-8)
- Fanger, P. O. (1972). *Thermal Comfort: Analysis and Applications in Environmental Engineering*. McGraw-Hill.
- VDI 3787 Part 2 (2008). *Methods for the human-biometeorological evaluation of climate and air quality for urban and regional planning.*
- Perez, R., et al. (1990). Modeling daylight availability and irradiance components. *Solar Energy*, 44(5), 271–289.
- Konarska, J., et al. (2014). Transmissivity of solar radiation through foliage of urban trees. *Int. J. Biometeorology*, 58(3), 415–426. [doi:10.1007/s00484-013-0632-4](https://doi.org/10.1007/s00484-013-0632-4)

**Urban climate, wind, and heat mitigation**
- Oke, T. R. (1987). *Boundary Layer Climates* (2nd ed.). Routledge.
- Macdonald, R. W., Griffiths, R. F., & Hall, D. J. (1998). An empirical model for mean velocity profiles within and above urban canopies. *Atmospheric Environment*, 32(11), 1857–1865.
- Buck, A. L. (1981). New equations for computing vapor pressure and enhancement factor. *J. Applied Meteorology*, 20(12), 1527–1532.
- Erell, E., et al. (2014). Effect of high-albedo materials on pedestrian heat stress in urban canyons. *Urban Climate*, 10, 367–386. [doi:10.1016/j.uclim.2013.10.005](https://doi.org/10.1016/j.uclim.2013.10.005)
- Middel, A., et al. (2019). Solar reflective pavements: heat mitigation strategy or thermal hazard? *Environmental Research Letters*, 14(9), 094016. [doi:10.1088/1748-9326/ab3299](https://doi.org/10.1088/1748-9326/ab3299)
- Taleghani, M. (2018). Outdoor thermal comfort by green infrastructure: a review. *Renewable and Sustainable Energy Reviews*, 81, 2188–2202.
- Santamouris, M. (2014). Cooling the cities — a review of reflective and green roof mitigation technologies. *Solar Energy*, 103, 682–703.
- Nazarian, N., et al. (2022). Integrated urban biometeorology for thermal equity. *Nature Communications*, 13, 4125. [doi:10.1038/s41467-022-31786-y](https://doi.org/10.1038/s41467-022-31786-y)

---

*OpenUBEM — outdoor analysis reference. A living registry: every new outdoor metric is recorded here
first (§8). The plan docs remain the binding specification for how each one is built.
Opened 2026-07-23 with UTCI as the first entry.*
