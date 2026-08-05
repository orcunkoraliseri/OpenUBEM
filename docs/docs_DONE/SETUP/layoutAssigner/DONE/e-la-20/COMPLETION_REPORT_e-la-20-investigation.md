# E-LA-20 Root-Cause Investigation — Completion Report

**Date:** 2026-07-25 · **Plan:** `PLAN_e-la-20_investigation.md` (I01–I05 + CP-INV) · **Status:** investigation complete, findings synthesized, **awaiting manager scoping of a follow-up implementation plan**.

**No fix has been implemented.** `git status --short openubem/ tests/` was verified clean after every task: zero production-code changes across the entire investigation. Every candidate fix shape below is a *candidate only* — none adopted, none partially wired in.

---

## 1. Per-task outcome table

| Task | Outcome | Load-bearing result |
|---|---|---|
| **I01** — local repro | ✅ 11/11 reproduced | Fatal reproduces locally on real EnergyPlus 23.1 across a **65× range of scale factor S** (0.0428 → 2.7789) at an identical `u_roof_w_m2k = 0.119`. **S is not the driver.** |
| **I02** — mechanism isolation | ✅ 12/12 runs, stop condition NOT met | (a) no patch **PASS**, (b) `thermal_mass=False` (`MATERIAL:NOMASS`) **PASS**, (c) `thermal_mass=True` (`MATERIAL`) **FATAL**, on 4 buildings spanning the S range. `thermal_mass=True` is the sole trigger. |
| **I03** — numeric regime | ✅ clean threshold found | Fails iff `u_roof < ~0.1380 W/m²K` ⇔ `Thickness > ~0.8698 m` ⇔ `Fo < ~1.785e-4`. 25 real runs, fully monotonic, ~0.2% bracket. |
| **I04** — why this cell | ✅ genuine outlier, driven by vintage | Same base U (0.119) in 4A and 6A — the discriminant is `VINTAGE_U_FACTORS`, not the climate zone and not S. `nyc_rural`'s S range is one of the *narrowest* of all 12 cells. |
| **I05** — mitigation probes | ✅ 30/30 probe runs PASS | Four distinct fix shapes all clear the Fatal; all agree on EUI to <1%. |
| **CP-INV** — synthesis | ✅ this report | Root cause confirmed, fleet exposure quantified, candidates ranked. |

All pass/fail claims in the plan's §7 are backed by verbatim `.err`/`.end` text. The director independently re-opened raw output files on disk for I01, I02, both of I03's bisection boundary runs, and I05's probe runs, rather than trusting any employee's printed summary.

---

## 2. I02 — the load-bearing mechanism-isolation result

4 buildings × 3 variants, all through the real pipeline, all run on real EnergyPlus 23.1.

| Building | S | (a) no envelope patch | (b) patched, `thermal_mass=False` | (c) patched, `thermal_mass=True` |
|---|---|---|---|---|
| way/772627076 | 0.0428 | PASS | PASS | **FATAL** |
| way/772627017 | 0.2879 | PASS | PASS | **FATAL** |
| way/772627020 | 0.5141 | PASS | PASS | **FATAL** |
| way/270445755 | 2.7789 | PASS | PASS | **FATAL** |

Variant (b) verbatim `.end`: `EnergyPlus Completed Successfully-- 260066 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  6.14sec` (0 CTF lines in its `.err`).
Variant (c) verbatim: `** Severe ** CTF calculation convergence problem for Construction="LA_ROOF_CONSTRUCTION"` → `**  Fatal  ** Program terminated for reasons listed (InitConductionTransferFunctions)`.

The plan's single stop-and-report condition (variant (b) also failing) did **not** fire. The "T03's fix is the trigger" framing holds.

---

## 3. I03 / I04 — numeric regime and cell concentration

### A clean threshold exists — stated plainly, not overstated

| | `u_roof` (W/m²K) | `Thickness` (m) | `Fo` | Result |
|---|---|---|---|---|
| FATAL side of bracket | 0.137813 | 0.870745 | 1.781e-4 | `EnergyPlus Terminated--Fatal Error Detected... 0.09sec` |
| PASS side of bracket | 0.138125 | 0.868778 | 1.789e-4 | `EnergyPlus Completed Successfully... 5.69sec` |

25 real EnergyPlus runs (20-point coarse sweep + 5-step bisection), **zero non-monotonicity**. `Fo = α·Δt/L²`, `α = k/(ρ·cp) = 0.12/(800·1000) = 1.5e-7 m²/s`, `Δt = 900 s` (4 timesteps/hour, read from a real generated IDF — not assumed).

### Why `nyc_rural` `SmallOffice` — vintage, not climate zone, not S

`SmallOffice`'s base roof U-value is **banded**: 0.153 (zones 1A-3C), **0.119 (zones 4A-6B)**, 0.097 (zones 7-8). `nyc_rural` (6A) and `nyc_centre`/`nyc_urban`/`nyc_suburban` (4A) therefore share the *same* base value. The discriminant is the vintage multiplier:

| Population | Vintage | Factor | `u_roof` | `Thickness` | vs. 0.8698 m threshold | Result |
|---|---|---|---|---|---|---|
| `nyc_rural` SmallOffice (150) | `90.1-2013` | 1.0 | 0.119 | **1.0084 m** | **+15.9% past the cliff** | FATAL |
| other 3 NYC cells' SmallOffice | `DOERefPre1980` | 1.6 | 0.190 | 0.6303 m | −27.5% (safe) | PASS |
| zones 4A-6B at `90.1-2007`/`2010` | — | 1.309 | 0.1558 | 0.7703 m | **−11.4% (thin margin)** | PASS |

`nyc_rural`'s S range is one of the **narrowest** of the 12 cells (max 2.78; eight other cells reach up to 7.6 and all pass) — the "incidental concentration of extreme-S buildings" hypothesis is disproved with data, not assumed away.

I04 traced the vintage one step further: `nyc_rural` carries exactly **one** real observed `year_built` among its 150 `SmallOffice` buildings; that single value becomes the Tier-2 group-mode donor for the other 149. The defect is deterministic and fully reproducible — but its evidential basis is a single OSM tag.

### Fleet exposure — the finding no single task was scoped to produce

Applying I03's threshold to the bundled construction table across every `(archetype_id, climate_zone, vintage)` combination:

> **204 of 3,248 combinations (6.3%) fall below `u_roof = 0.138` and would Fatal under `thermal_mass=True`** — spanning **6 archetypes** (`SmallOffice`, `SmallOfficeDetailed`, `FullServiceRestaurant`, `QuickServiceRestaurant`, `SmallDataCenterHighITE`, `SmallDataCenterLowITE`), **10 climate zones** (4A through 8), and **5 vintages** (`90.1-2007` through `90.1-2019`).

E-LA-20 is therefore **not** a `nyc_rural` curiosity. It is a latent structural exposure that the 12-cell validation fleet happened to expose in exactly one cell, because that fleet contains almost no modern-vintage buildings in cold zones. Any future fleet containing modern-vintage small commercial buildings in zones 4-8 hits the same Fatal.

### Scope correction to E-LA-20 itself

The affected population is **150/150 = 100%** of the genuine `nyc_rural` `SmallOffice` buildings, **not** "150/154 = 97.4%". The 4 exceptions are exactly the 4 `building_tag="hotel"` buildings in that cell — all four with `levels=NaN` and `year_built=NaN` — which classify as `SmallHotel` at current HEAD; two of them are the already-documented E-LA-17/E-LA-15 carryovers. The "4 survivors" never constituted evidence of a passing sub-regime. See §8 **E-LA-22**.

---

## 4. I05 — mitigation probes (candidates only, none adopted)

3 buildings spanning S × 10 probe variants = **30/30 PASS**. No probe reproduced the CTF Fatal.

| Probe | Result | Runtime | EUI vs. other probes |
|---|---|---|---|
| **(a)** multi-layer split, N=2 / 4 / 8 | PASS at every N | ~5.8-6.2 s | within 0.01% across N |
| **(b)** `ConductionFiniteDifference` | PASS | **112-124 s (~20×)** | within 0.4% |
| **(c1)** R-preserving thickness cap (0.5/0.3/0.2/0.1 m) | PASS at every cap | ~5.8-6.1 s | within 0.3% |
| **(c2)** hybrid thin-mass + NOMASS residual (0.20 / 0.10 m) | PASS at both | ~5.9-6.0 s | within 0.1% |

**EUI comparison** against the old `thermal_mass=False` behaviour (same 9-meter formula, same buildings):

| Building (S) | `MATERIAL:NOMASS` EUI | probes' EUI range | spread among probes | vs. NOMASS |
|---|---|---|---|---|
| way/772627076 (0.043) | 153.212 | 149.00 – 149.85 | 0.57% | 2.2-2.8% lower |
| way/772627020 (0.514) | 81.108 | 79.52 – 79.84 | 0.40% | 1.6-2.0% lower |
| way/270445755 (2.779) | 70.251 | 69.24 – 69.52 | 0.41% | 1.0-1.4% lower |

**All fix shapes are numerically indistinguishable at the EUI level.** The choice among them is about fidelity to intent, implementation complexity and runtime — not about the answer.

**Plan-text correction applied (director ruling, logged in §7).** Plan I05(c) proposed "a minimum-`Thickness` clamp higher than the current 0.01 m floor". That is inapplicable: the failing thickness is 1.008 m, ~100× *above* the 0.01 m floor, so raising a minimum floor cannot affect it. Probe (c) was replaced with the two upper-bound variants (c1)/(c2) above.

**Honesty note carried from I05:** the employee's first (a) N=2/N=4 attempt produced a *different* Fatal (`Did not find matching material for Construction LA_ROOF_CONSTRUCTION, missing material =`) caused by a bug in its own scratch script writing explicit blank `Layer_N` fields — not an EnergyPlus or `openubem/` finding. Fixed and rerun; reported rather than smoothed over.

---

## 5. Root cause — plain language

`patch_envelope()` builds each opaque assembly by holding conductivity fixed at `_K = 0.12 W/m·K` and letting **thickness absorb the entire target R-value** (`Thickness = max(0.01, (1/u) * 0.12)`). That inversion is harmless while the layer is `MATERIAL:NOMASS`, because a massless layer is a pure resistance and EnergyPlus never computes a conduction-transfer-function series for it. The structural-fixes plan's T03 fix switched `layout_assign` to `thermal_mass=True`, which turns exactly the same geometry into a real `MATERIAL` with `Density=800 kg/m³` and `Specific_Heat=1000 J/kg·K`. For a well-insulated roof this yields a single homogeneous slab **over a metre thick** carrying roughly 800 kg/m² — a thermal time constant far beyond anything EnergyPlus's CTF solver can expand into a stable series at the model's 900 s timestep, so `InitConductionTransferFunctions` fails outright, before Warmup or Sizing, in about 0.1 s. The failure is governed by the Fourier number `Fo = α·Δt/L²` and appears sharply and monotonically once `Fo` drops below ~1.785e-4, i.e. once `u_roof` drops below ~0.138 W/m²K. This is the **thick, high-mass** branch of EnergyPlus's own CTF diagnostic text — not the "very thin, highly conductive" branch the original E-LA-20 log entry leaned toward — and it has nothing to do with the scale factor S, which the original entry hypothesized and which I01 disproved across a 65× range.

---

## 6. Recommendation for a follow-up implementation plan

**Do not** treat this as a `nyc_rural` patch. The fleet-exposure derivation in §3 shows 204 at-risk `(archetype, zone, vintage)` combinations across 6 archetypes and 10 climate zones; a fix scoped to one cell would leave the rest latent.

A follow-up plan should contain, at minimum:

1. **A pre-decided fix shape, chosen between I05's (a) N=2 split and (c2) hybrid.** Both preserve total R exactly and clear the Fatal with wide margin. **(a) N=2 is the recommended starting candidate**: it preserves total R *and* total thermal mass exactly by construction, making it the most faithful to the intent of the `thermal_mass=True` fix that E-LA-20 came from, and it is the smallest structural change to `envelope_patcher.py`. **(c2)** is the recommended fallback if fleet-scale testing shows N=2 is insufficient at the extreme low-U end (zones 7-8 at modern vintage reach `Thickness=1.237 m`, well past what this investigation's 3-building probe sample covered — a plan should verify the chosen N holds there, or make N adaptive to `r_val`).
2. **A guard derived from I03's threshold, not from a hard-coded cell name** — the condition `Thickness > ~0.87 m` (equivalently `u_roof < ~0.138`, equivalently `Fo < ~1.785e-4` at Δt=900 s) is the real predicate. Note the threshold is timestep-dependent; a plan should state whether it re-derives it or pins Δt.
3. **A fleet-scale verification task**, because this defect was invisible to every ≤28-building local sample across two prior plans and surfaced only at 8,160-building scale. Local repro is necessary but demonstrably not sufficient.
4. **`(b) ConductionFiniteDifference` explicitly rejected as the primary fix** — it works, but at ~20× runtime, which is prohibitive at fleet scale. Fallback only.
5. **A decision on the two carried-forward defects** logged in this plan's §8: **E-LA-21** (dead `has_fatal` column — trivial, reporting-only) and **E-LA-22** (T19 archetype/vintage non-reproducibility for data-poor buildings — material for any future cross-generation fleet comparison, and arguably its own arc).

**Not drafted here.** Authoring that plan is a separate, manager-scoped task, per this investigation's own §1 rule 9.

---

## 7. Open questions this investigation could not resolve

1. The exact causal chain behind **E-LA-22**'s archetype/vintage divergence at current HEAD. Dates and file paths implicate the 2026-07-25 semantic-imputation commit (`3a925f9`, landing *after* the 2026-07-24 T19 run, touching `imputation.py`/`spatial_impute.py`, with all four affected buildings being exactly the ones whose classifier inputs come from imputation) — but the chain itself is **unproven** and was deliberately not chased.
2. Whether the 204 at-risk combinations should be addressed at the material-construction level (I05's probes) or upstream, by questioning whether a single-layer `Thickness = R·k` inversion is the right envelope model at all once mass is real. That is a DESIGN-level question this investigation deliberately did not open.
3. Whether the `CheckWarmupConvergence` severes (already-logged E-LA-14/E-LA-19 class) seen alongside several passing probes are *surfaced* or *caused* by them. I05 flagged the distinction honestly and did not resolve it.
