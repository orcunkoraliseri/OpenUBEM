# RESULT — Phase-E CP-D Go/No-Go ruling (la_urban pilot)

- **Date:** 2026-06-27 (overnight, manager-autonomous under user's "auto-proceed if clean" delegation)
- **Author:** Manager (Opus)
- **Inputs:** `REPORT_phaseE_pilot.md` (auto-generated), per-archetype audit of `docs/validations/overAll/results/phaseE/la_urban/05_results.gpkg`, sim_out `.end`/`.err` inspection.
- **Gate:** CP-D = 🔴 hard gate before the 12-cell fan-out (T17).

## VERDICT: **NO-GO — HOLD at CP-D. Fan-out NOT launched.**

The pilot did **not** clear all three technical gates cleanly, so the user's "auto-proceed if clean" condition is not met. Two real defects must be fixed and one gate re-specified before the 8,160-building fan-out. Importantly, the core Phase-E thesis is **partially vindicated** (see §"Wins"), so the path forward is fix-and-proceed, not abandon.

---

## What actually happened to the pilot run

The detached pilot process (PID 26108) shipped 618 buildings to Speed, EnergyPlus simulated **617/618**, then the local driver `v12_cell_pipeline.run_cell` hit its **zero-fail `sys.exit(2)`** (lines 1025–1030) because 1 building was unsimulatable — so it terminated **before Step 5 ran**. No results/report were produced by the pilot itself. The manager recovered the run by re-executing Step 5 + rescore from the 617 on-disk `.sql` files (no re-sim, no cluster) → `aggregate_results` completed in 740 s, gpkg + report written. All numbers below are from that recovered parse.

---

## Gate-by-gate

### Gate 1 — sim-success ≥ Phase-D rate (~100%): **MET** (with a caveat)
- Phase-E **617/618 = 99.84%**; Phase-D2 was 618/618.
- The 1 failure is `way/402215469` (**Warehouse**, rerouted to one_zone_per_floor) — E+ fatal `Indicated Zone Volume <= 0.0` + dozens of "floor/roof upside down". A **degenerate-geometry collapse**, NOT a central-plant autosizing failure. Phase-D simulated it fine, so this is a 1-building geometry regression introduced by Phase-E's geometry routing.
- Not a No-Go by itself, but it exposes a **fan-out blocker** → see Blocker B2.

### Gate 2 — fans+pumps median in 12–16 kWh/m²: **FAILS AS WRITTEN, but is a gate-spec artifact (physics PASSES)**
- Whole-cell median fans+pumps = **7.32** (fans 7.32, pumps 0.00) → outside 12–16.
- **But pumps are correct.** Per-archetype: pumps>0 for **every** central-plant building — LargeOffice 37/37 (median 10.3), HighriseApartment 10/10 (3.9), TallBuilding 4/4 (8.4), PrimarySchool 2/2 (18.1), Courthouse 1/1 (0.8) — and correctly 0 for packaged-system archetypes (MediumOffice/SmallOffice/MidriseApartment/Retail/restaurants/SuperMarket/Warehouse → PSZ/PTAC, no plant). The whole-cell median is ~0 only because **73% of la_urban is MidriseApartment** (446/615).
- Central-plant-subset fans+pumps median = **34** kWh/m². The 12–16 band fits neither the residential median (~7) nor the central-plant median (~34).
- **Ruling:** the 12–16 band (from RESULT_02 Part C) was a prior for central-plant buildings, mis-applied to a residential-dominated cell median. The pump/fan physics is sound. **Re-specify the gate** (evaluate per-archetype, or on the central-plant subset) — this is NOT a physics blocker.

### Gate 3 — no end-use blowup / refrig 100–350 / total finite-sane: **MIXED → one real blowup**
- **Refrigeration: PASS.** SuperMarket `way/376149058` refrig **115.9**, total **311.4** → PLAUSIBLE. R-CP-B-1 defrost fix holds on real geometry; the pilot watch-item ("may under-predict") did not materialize — 115.9 is within band and total 311 is a sensible supermarket. No calibration action needed.
- **Cooking: PASS.** Nonzero exactly where expected — FullServiceRestaurant 212, QuickServiceRestaurant 475, PrimarySchool 6; zero elsewhere.
- **🔴 BLOWUP — PrimarySchool heating runaway.** Both PrimarySchools are pathological: heating **760–1256 kWh/m²**, fans **285–444**, total **1392–2175** (the 2175 is the single worst outlier in the cell). In mild LA (3B, near-zero heating need) this is physically impossible. E+ completes with **0 severe** (so zero-fail can't catch it), `.err` shows a benign heating-setpoint schedule type-limits warning + a zero-flow autosize on a heating coil. Signature = **reheat / simultaneous-heating-cooling runaway** in the central-VAV + HW-reheat school family. Only 2 buildings here, but it is a **systematic archetype defect** that will corrupt schools across all 12 cells. → Blocker B1.

---

## Wins (why this is fix-and-proceed, not abandon)
- **CBECS NMBE: −39.3% (Phase-D2) → −3.1% (Phase-E) — now PASS.** Physically modelling the service loads (DHW/cooking/refrig/fans/pumps) **centered the distribution bias** — the central payoff we hoped for. This is the strongest evidence yet that the realism path is the right one.
- **Median total 104.68 vs LA EBEWE 113.6 = −7.9%** — strong central tendency with **zero fitting / zero reconstruction**.
- Refrigeration, cooking, pumps, fans all instantiate and meter correctly per archetype.

## Honest caveats (as predicted to the user)
- **R² regressed 0.71 → 0.40.** Outliers (PrimarySchool 2175, restaurants ~900–1300) crush R²; fixing B1 should recover much of it.
- **CV(RMSE) 58% and KS 0.32 still FAIL (shape).** Structural archetype-determinism vs per-building survey spread — consistent with the standing report-only stance. Physical objects added some variance (good for realism) but not enough to clear the shape gates.

---

## Watch-item to verify before/with fan-out (not a blocker)
- **DHW fuel inconsistency.** MidriseApartment DHW = **all-electric** (31.9 kWh/m², the dominant 446-building archetype), but HighriseApartment DHW = **all-gas** (29.3). Both are multifamily residential; DOE prototypes typically use gas SWH for both. This materially affects EUI and carbon for the dominant archetype. Verify the DHW fuel assignment in the Phase-E service-load tables against the prototypes; correct if it's an assignment error.

---

## Required before T17 fan-out

| # | Item | Type | Action |
|---|---|---|---|
| **B1** | PrimarySchool (likely SecondarySchool too) heating/reheat runaway (760–1256 kWh/m²) | 🔴 defect | Root-cause the school central-VAV+HW-reheat family (heating setpoint schedule values/type-limits, VAV min-airflow reheat fraction, HW-loop control, zero-flow heating-coil autosize). Re-sim the 2 la_urban schools to confirm school heating lands in a sane band before fan-out. |
| **B2** | Zero-fail `sys.exit(2)` will hard-kill any cell with ≥1 unsimulatable building, wasting the cluster run | ⚙️ pipeline blocker | Make `run_cell` tolerate a small number of **logged** geometry drops (PLAN T17 forbids *silent* drops, not logged ones). Log each dropped osm_id + reason; proceed to Step 5 on the survivors. |
| **G2** | Gate-2 fans+pumps band 12–16 is mis-specified for mixed cells | 📏 gate spec | Re-specify: evaluate fans+pumps per-archetype or on the central-plant subset, not the whole-cell median. |
| **W1** | MidriseApartment electric vs HighriseApartment gas DHW | 🔎 verify | Confirm DHW fuel against DOE prototypes; fix table if wrong. |

After B1 + B2 (and ideally W1), re-run the la_urban pilot to confirm the school blowup is gone and the zero-fail path is clean, **then** fan out the remaining 11 cells.

---

## Manager note on the delegation
User pre-authorized auto-fan-out **iff** all three gates passed cleanly. They did not: Gate 3 has a real school-HVAC blowup, Gate 2 needs re-specification, and a fan-out pipeline blocker surfaced. Holding is the correct application of the user's "any fail → HOLD, write Go/No-Go" instruction. No commits (git external). Awaiting user greenlight on the B1/B2/G2/W1 plan.
