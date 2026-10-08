# DECISION REQUEST D-EU-35 — EU-13's geometry_outcome no longer matches what was actually simulated; a real re-simulation is required, not optional

- **Date:** 2026-08-28
- **Arc:** European locations x Step 8
- **Record:** `openubem/outputs/eu_evidence/EU-13/RESULTS_EU-13.md` §7; this DR
- **Blocks:** trusting `heating_kwh`/`eui_kwh_m2` for any building whose `geometry_outcome` changed under EU-13
- **Status:** RULED (Option 1 selected) — resimulation on Speed authorised to restore geometry/physics sync

---

## 1. The one-sentence version

`scripts/emit_eu11_layout_sidecars.py` (EU-13) recomputes `geometry_outcome` and the pop-up's dwelling zones
from the footprint alone, independent of what actually ran on EnergyPlus at EU-11; for the ~1,077 buildings
whose label changed, the published `heating_kwh`/`floor_area_m2`/`eui_kwh_m2` still reflect the **old**
zoning (mostly the massing-box fallback, or the pre-fix storey-0-only dwelling zones), not the new one.

## 2. How this was found and confirmed (measured, not inferred)

- `scripts/run_eu_s2_district_campaign.py:_geometry` is the function that actually built the zones EnergyPlus
  ran — a **separate, independent recomputation** from the side-car emitter, sharing only the underlying
  `generate_european_dwelling_layout`/`european_layout_to_zone_specs` library calls.
- At EU-11 harvest time, its dwelling-layout branch called `european_layout_to_zone_specs(...)` **without**
  `n_storey=n_storey` (same bug as `FINDING EU-12-01`, but here it produced the real submitted IDF, not just a
  side-car), and its `else` branch had no dwelling-count imputation — any building with a missing observed
  count went straight to the massing-box fallback.
- Spot check: `relation/12582232` (Madrid, 4 storeys) — manifest `floor_area_m2 = 1089.2873` exactly equals
  `272.32 m² x 4`, i.e. the harvested run's floor area already reflects 4 full storeys. This is the
  **massing-box** total, not a coincidence: EU-13's side-car script re-evaluated this footprint fresh, found
  the (now-extended) general partition algorithm could subdivide it, and overwrote `geometry_outcome` to
  `DWELLING_LAYOUT_EMITTED` in the manifest — but `heating_kwh` was never recomputed under that partition.
- Fixed `_geometry()` to match the side-car emitter exactly (`n_storey` stacking + the same four-tier
  imputation cascade, ported in): verified directly on `relation/12582232` — now produces 20 zones (4 storeys
  x 5 dwellings), `outcome = DWELLING_LAYOUT_EMITTED`, matching the side-car. No IDFs were regenerated or
  submitted; this is a code fix only, verified by direct function call, not by a new campaign run.

## 3. Scope of the desync

Every building whose EU-13 `geometry_outcome` differs from what was actually harvested at EU-11's Speed run.
Bounding this precisely requires comparing the two `geometry_outcome` histories (not yet done); the ceiling is
EU-13's full reported coverage increase — up to 1,027 of the 1,078 buildings now labelled emitted (all beyond
the original 51). Bologna is unaffected (0 simulated either way).

## 4. Ruling

- [x] **Option 1 (Adopted) — Regenerate IDFs via the now-fixed `prepare()` and resubmit the affected buildings to Speed**,
   harvest, and overwrite `heating_kwh`/`floor_area_m2`/`eui_kwh_m2` for every building whose `geometry_outcome`
   changed — restoring label/physics consistency. Scale: up to ~1,027 buildings across Madrid/Lyon/London,
   `sbatch --array`, same EnergyPlus 23.1.0 Ubuntu20 Speed pipeline as EU-11.
- [ ] **Option 2** — Do nothing yet; leave the desync documented and flagged in the viewer until a later arc.

> **RULING:** Option 1 approved. Regenerate the IDFs for all buildings whose `geometry_outcome` changed under EU-13 using the synchronized `prepare()` pipeline (`n_storey` stacking + imputation cascade), resubmit the batch to the Speed cluster, harvest verified thermal outputs (`heating_kwh`, `floor_area_m2`, `eui_kwh_m2`), and update `RESULTS_EU-11.md` and external validation records accordingly.
>
> **Owner name / initials:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

Timing note: This re-simulation is independent of `EU-14` (Bologna) — they may proceed in parallel or in either sequence.

## 5. What must never happen

- No re-harvest that silently overwrites `heating_kwh` without also updating `RESULTS_EU-11.md`'s pooled EUI
  figures and the DR12-16 external-validation verdicts that were checked against the old numbers.
- No partial resubmission that leaves some `DWELLING_LAYOUT_EMITTED`-labelled buildings still running on
  stale massing-box physics without a flag.

## 6. Next free identifier

`D-EU-35` consumed today. Next free identifier `D-EU-36`.

