# DECISION REQUEST D-EU-17 — every zone ran with a 10 m³ volume

- **Date:** 2026-08-26
- **Arc:** European locations × Step 8 boundary closure
- **Record:** `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.17
- **Finding:** **EU-S2-07** (new), caveat **C-20**
- **Found while:** executing your Q3 ruling on G8.15 — by reading what the six approved warning kinds say
- **Blocks:** any use of the S2 heating number; does **not** block the boundary specification
- **Status of the Q3 ruling:** executed for four kinds, **held for two**. G8.15 stays `FAIL`.

---

## 1. The one-sentence version

EnergyPlus calculated a **negative** volume for every zone in every building, substituted a fixed
**10.0 m³**, and because ventilation is specified in **air changes per hour**, the ventilation heat loss
in the S2 run is understated by **at least 19.2×**. The reported **31.2144 kWh/m²** was computed with
almost no ventilation losses.

## 2. What EnergyPlus actually said

From `openubem/outputs/eu_evidence/EU-04/s2_campaign/BATIMENT0000000013365727_part0/eplusout.err`:

```
** Warning ** Indicated Zone Volume <= 0.0 for Zone=BATIMENT0000000013365727_PART0_F0_WHOLE
**   ~~~   ** The calculated Zone Volume was=-49.03
**   ~~~   ** The simulation will continue with the Zone Volume set to 10.0 m3.

** Warning ** GetVertices: Floor is upside down! Tilt angle=[0.0], should be near 180,
              Surface="BLOCK ... STOREY 0 FLOOR 0001"
```

The second warning names the cause: the floor surfaces have reversed vertex order, so the enclosed
volume comes out negative. The `Zone` object requests `autocalculate` for Ceiling Height, Volume and
Floor Area, so nothing in the IDF overrode the substitution.

## 3. The measurement

| | |
|---|---|
| Zones affected | **103 of 103**, in **31 of 31** buildings |
| Calculated volume | **always negative** — −27.44 m³ to −408.41 m³ |
| Volume actually simulated | **10.0 m³**, every zone, without exception |
| Total air volume simulated | **1 030 m³** |
| Total air volume implied by the geometry | **19 823.7 m³** |
| **Understatement factor** | **19.2× aggregate**; 2.7× to 40.8× per zone |

## 4. Why it changes the number

The ventilation object in every IDF:

```
ZONEVENTILATION:DESIGNFLOWRATE,
    EU_ConstantAir_..._F0_whole,
    ...
    AirChanges/Hour,          !- Design Flow Rate Calculation Method
    ,                         !- Design Flow Rate
    ,                         !- Flow Rate per Floor Area
    ,                         !- Flow Rate per Person
    0.5670844752155818,       !- Air Changes per Hour
    Natural,                  !- Ventilation Type
```

EnergyPlus converts air changes per hour into a flow as **ACH × zone volume ⁄ 3600**. The volume is the
multiplier. At 10 m³ instead of the true value, the outdoor air entering each zone — and with it the
energy needed to heat that air from outdoor to setpoint — is reduced by the same factor.

Ventilation loss is a first-order term in residential heating demand. **The S2 headline of
31.2144 kWh/m² was therefore computed with essentially no ventilation heat loss.** The sign of the error
is not in doubt: the true figure is materially **higher**.

## 5. A sharper reading of the same numbers

The implied volumes sum to **19 823.7 m³**. The reported modelled floor area is **19 823.6173 m²** —
equal to four significant figures.

The volume the geometry produces is therefore **floor area × 1.0 m**, not floor area × a storey height.
So even the negative magnitude is not the true volume; the geometry is producing **1 m-tall zones**. The
19.2× is a **floor** on the error, not an estimate of it. With a realistic 2.5 m storey height the
ventilation understatement would be closer to 48×.

This also touches caveat C-14: the denominator is modelled zone floor area. The floor area appears
sound — it is the third dimension that is not.

## 6. Why the Q3 ruling was held for two kinds

You approved the six observed warning kinds as benign. Four of them are:

| Kind | Reading |
|---|---|
| `calculated design cooling load for zone` | Consistent with C-01 — heating is the only requested end use |
| `managesizing` | No `Sizing:Plant` object; plant sizing skipped, and there is no plant loop |
| `processscheduleinput` | `Schedule:Constant="EU_ALWAYSON"` has no type-limits name; not validated |
| `gethtsurfacedata` | Ground-coupled surfaces with no `Ground Temperatures` input — **EnergyPlus says *"Defaults, constant throughout the year of (18.0) will be used"***. Benign as a warning, but it is an assumption a heating study must **state**, not inherit silently |

The other two — `indicated zone volume <` and `getvertices` — are the same defect seen from two angles,
and they are **not** benign. Approving them would make G8.15 pass over the one finding it earned.
**G8.15 exists for exactly this.** Marking it green here would convert a working gate into a decoration.

So the Q3 ruling is executed for the four kinds above and **held** for these two, pending your answer
below.

## 7. What this does and does not affect

**Affected:** the S2 evidence bundle — the 31 buildings, the 618 782.3181 kWh, the 31.2144 kWh/m², and
every statement derived from them, including the 5-building / 26-building geometry split in C-03.

**Not affected:** the 510-cell campaign specification. It contains no simulation results. Its cells,
identifiers, archetypes, `f` ladder, weather fields and caveat register are untouched by this.

**But:** the same geometry path would produce the same defect for `es`, `uk` and `it`. This is a pipeline
defect, not a blemish on one bundle. Anyone who executes the frozen contract inherits it.

## 8. Options

### (a) Repair the geometry, re-run S2, restate the number — **RECOMMENDED**

Fix the floor-surface vertex order so volumes come out positive, and set a real storey height so zone
volume is floor area × storey height rather than floor area × 1 m. Re-run the 31 buildings, restate
31.2144 with the superseded value preserved, and let G8.15 be scored honestly on the result.

- Cost: one geometry pass plus a 31-building re-run (minutes, locally).
- The only option that produces a heating number anyone can quote.
- The freeze is unaffected and can proceed in parallel — this is not on the boundary's critical path.

### (b) Repair the geometry, do not re-run

Fix the defect so the frozen contract is executable correctly by whoever runs it, and **withdraw** the
S2 number entirely rather than restating it.

- Cheaper; honest.
- Cost: the arc ends with no demonstrated end-to-end result at all.

### (c) Record and ship

Leave the geometry, keep G8.15 `FAIL`, carry C-20, and hand over as is.

- Cost: the receiving team inherits a pipeline that silently simulates 10 m³ zones. C-20 says so, but a
  caveat is not a repair, and this one is the kind that gets read after the results are published.

## 9. Recommendation — (a)

The defect is measured, its cause is named in EnergyPlus's own words, and its magnitude has a floor of
19.2×. It is cheap to fix and cheap to verify: after the repair, the zone volumes must be positive and
`sum(volume) ≈ floor_area × storey_height`, which is a one-line check.

(c) is the only option that leaves a known-wrong pipeline in someone else's hands, and it is the one I
would argue hardest against — the whole point of the caveat register is that it records what could not be
fixed, not what was not fixed.

**One thing that holds whichever you choose:** 31.2144 kWh/m² must be withdrawn from circulation now. It
is not a figure with a wide uncertainty band; it is a figure computed with a first-order loss term
missing.

## 10. Where to check this

| Path | What it shows |
|---|---|
| `openubem/outputs/eu_evidence/EU-04/s2_campaign/*/eplusout.err` | The negative volumes and the 10.0 m³ substitution, 103 times |
| `openubem/outputs/eu_evidence/EU-04/s2_campaign/*/*.idf` | `ZONEVENTILATION:DESIGNFLOWRATE` with `AirChanges/Hour` = 0.567, and `Zone` with `autocalculate` volume |
| `openubem/outputs/eu_evidence/EU-10/s2_dossier/s2_dossier.json` | The 31.2144 kWh/m² headline this affects |
| `openubem/data/campaign/eu_boundary_caveats_v1.0.json` | C-20, and the amendment on C-08 |
| `docs/docs_ACTIVE/europeanLocations/MVP_european_locations.md` §12.17 | FINDING EU-S2-07 |

**Answer:** **(a) Repair, re-run, restate** ☑   **(b) Repair, withdraw the number** ☐   **(c) Record and ship** ☐

**RULING:** Option (a) approved. Repair floor-surface vertex order and ensure exact storey height in IDF geometry generation so that EnergyPlus computes true positive zone volumes (volume = floor area × storey height). Re-run S2 simulation on the 31 buildings, restate the heating demand and fleet EUI with the superseded 31.2144 kWh/m² value preserved in provenance, and re-score gate G8.15 cleanly.

**Owner name / initials:** Project Lead / Evaluator  
**Date:** 2026-08-26

