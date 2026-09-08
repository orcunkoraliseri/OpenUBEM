# 4J → OpenUBEM — the `outputs_3D` layout payload is pre-carry-in and mostly missing. One ask, two questions.

**From:** 4J (GSSCanada) · **Date:** 2026-09-08 · **In reply to:** the `eu_FR-LYO-HAUTCOEURPENTES`
delivery
**Record:** `Step10_docs/impl/2026-09-08_openubem-3d-export-layouts-audit.md`

⚪ **Read-only on your tree. Nothing under `OpenUBEM/` was written.** No simulation, no re-run, no
job submission. No 4J gate was scored, no band moved, no manifest written. Step 10 campaign `C2`
still has **no cell**, and `prereg_step10_nocore_DRAFT.md` is still **DRAFT and unfrozen** — which
is deliberate: it must be frozen *before* the first district runs, not after.

🟢 **First, congratulations and an acknowledgement.** Read from your `STATE_european_locations_v5.md`
today, not from memory: the **engine carry-in is complete** (`european_nocore.py`, bit-parity
**0 mismatches on 2,529 / 2,529 compared plates** across all four districts), `D-EU-88` is
**complete**, `EU-19` is **complete**, and `D-EU-55` is satisfied by the ceiling82 campaign's own
submission. That closes **freeze condition 1** of our pre-registration. This letter is not a
complaint about the engine.

---

## 1. The ask — regenerate `outputs_3D/eu_*_data/layouts/`

This is the one thing blocking us. 4J reads the per-building layout payload
`outputs_3D/eu_<district>_data/layouts/*.json` for the per-dwelling population: `k`,
`units_per_floor`, `storeys` and the per-storey zone list. Two problems, both measured this morning.

### 1.1 🔴 It predates the carry-in by two days

**All four `layouts/` directories are dated 2026-09-01.** Every `buildings.csv` and `viewer.html`
beside them was regenerated **2026-09-07 / 2026-09-08**. The carry-in landed **2026-09-03**. So the
layout payload was not regenerated with its siblings, and the two now disagree for the same
building. Bologna `27746`:

```
buildings.csv  (2026-09-07)   circulation_pct 0.0
                              gross_area_m2 114.5 == conditioned_area_m2 114.5
layouts/27746.json (09-01)    has_unconditioned_core  true
                              circulation_area_m2_total  8.1972
                              gross_footprint_area_m2 136.8679 != conditioned_floor_area_m2 128.6707
```

Counts:

```
                    cored layout files      buildings.csv rows with circulation_pct > 0
Bologna             173 of 1,204            0 of 1,257
Lyon                 31 of   297            0 of   768
London                0 of     1            3 of 1,351
Madrid                0 of     2            0 of 1,398
```

Per-file cross-tab of top-level `scheme` against `has_unconditioned_core`:

```
Lyon      null 192 F | 1x1 72 F | 2x1 23 T | 3x2 6 T | 2x2 2 T | 2x2 1 F | 4x2 1 F
Bologna   null 979 F | 2x1 146 T | 1x1 47 F | i_shape_linear_gallery 11 T
          narrow_plate_corridor_free 10 T | l_shape_decomposition 5 F | 2x2 4 T | 3x2 2 T
```

⚪ Every cored file is multi-cell and no `1x1` is cored — but **seven multi-cell plates are already
core-free** (Bologna's five `l_shape_decomposition`, Lyon's `4x2` and one `2x2`), which reads like
2026-09-01 catching the cutter mid-migration rather than wholly before it.

🔴 **We are not reporting a live engine defect.** `european_nocore.py` is not accused of drawing
cores; the payload is simply older than it. We say this explicitly so the finding is not read as a
regression against your bit-parity result.

### 1.2 🔴 The two districts we most need ship almost no layouts at all

```
district                  residential   ruled (buildings.csv)   layout files shipped
eu_ES-MAD-BERRUGUETE            1,194                   1,038                     2
eu_GB-LDN-STDUNSTANS            1,242                     692                     1
eu_IT-BOL-GALVANI2              1,220                     552                 1,204
eu_FR-LYO-HAUTCOEURPENTES         530                     459                   297
```

Madrid declares 1,038 ruled buildings and ships **2** layout files; London declares 692 and ships
**1**. Both `buildings.csv` files are complete and current. **Madrid and London are two of our three
folds** (Spain, the UK, Italy), so this is a harder blocker for us than the cores are.

⚪ Also, Lyon's `sources.json` overstates its own payload: `layout_counts.ruled = 459` and
`layouts_coverage` reads *"459 dwelling layout ruled"*, but 297 files ship. **201 ruled buildings
have no layout JSON**, and **39 of the shipped files belong to `massing_box` buildings**
(258 ruled + 39 massing_box = 297). Worth a look at whichever writer emits that block.

### 1.3 ⚪ And one note on Lyon, so you do not spend effort in the wrong place

France is a **physical baseline** for 4J and never enters a 4J denominator — no French fold, no
French held-out fold, no French diary (`G10.11` / `G10N.11`, and the corpus is three countries).
Lyon's geometry is genuinely useful to us as a physical comparison and for one static rendering, but
**a per-dwelling occupancy campaign cannot run on it**. If you are prioritising regeneration,
**Madrid, London and Bologna are the ones that unblock 4J**; Lyon is not urgent.

---

## 2. Question one — `FINDING 258`, before or after the payload we consume?

Your §7 item 6 carries this open and unscheduled: some plates report `PASS ALL 7 CHECKS` yet divide
into a few tiny strip dwellings alongside one oversized dwelling absorbing the rest, because the
seven-check set does not penalise inter-dwelling area imbalance on the same plate. The owner's
ruling is per-affected-building repair, never a full-batch re-cut, and we are not asking for that to
change.

🔴 **We need the sequencing, not the fix.** 4J's Step 11 aggregates **per dwelling**, so an
imbalanced division changes what a dwelling *is* in our denominator. If the repair lands after we
have consumed a payload, our population silently changes underneath a frozen pre-registration.

**Please tell us one of two things:** (a) the repair will land before the next `layouts/`
regeneration, so we consume the repaired geometry; or (b) it will land after, in which case we will
record the affected building list as a declared limitation and hold the count fixed. Either is
workable. Not knowing which is not.

## 3. Question two — `D-EU-84`, because it is our freeze condition 2

Your §7 item 1 records `MAX_FLAT_ASPECT` as **not calibrated**: no rung of 2.5 / 3.0 / 3.5 / 4.0
reached `FAIL 0` after two genuine repair rounds, it is set to the strictest rung **2.5** per
`D-EU-89` clause 2, and **81 of 550 plates ship as an honest residual `FAIL` across 57 unique
buildings** — thick-band courtyard rings and dense `n = 12` multi-wing plates. `EU-21` acceptance
criterion 3 is **not met**.

🔴 **We are not asking you to make it pass.** An honest residual `FAIL` reported as one is exactly
what we would do. But our pre-registration's **condition 2 says `D-EU-84` and `D-EU-87` must be
ruled and closed**, and `D-EU-84` is neither. So: **is `D-EU-84` going to be closed as an accepted
residual (81 of 550, named), or is it still open work?** If it will be closed as an accepted
residual, say so and we will freeze against that wording and carry the 57 buildings as a declared
limitation. We will not move a threshold of ours to accommodate it, and we would ask that
`MAX_FLAT_ASPECT` not be moved to accommodate us.

⚪ `D-EU-87` we read as **implemented** — `C10` rebuilt as a created-pinch test. Confirm if that is
wrong.

---

## 4. What 4J will do, and will not do

* **Will:** once a regenerated payload lands for Madrid, London and Bologna, run a **shakedown** on
  Bologna alone. 🔴 A single district is **not a campaign** — our `G10N.19` needs 30 qualifying
  buildings **per fold** across three folds, so a one-district run scores nothing and moves no gate.
* **Will:** freeze the pre-registration **before** the first district runs, never after.
* **Will not:** read `k` or `N_u` from the current 2026-09-01 payload, because
  `circulation_area_m2_total > 0` contradicts `D-EU-80`'s every-square-metre-is-a-flat premise and
  would seed our population with core-era arithmetic.
* **Will not:** quote your pooled district EUI figures as 4J results. We have read them
  (Lyon 69.595307 over 505 of 509, London 120.064327 over 706, Madrid 80.694006 over 1,166 of 1,175,
  Bologna 54.935569 and stale pending its delta harvest) and they stay yours.
* **Will not:** ask for any EnergyPlus run, re-cut or re-simulation. Nothing in this letter requires
  compute beyond re-emitting a JSON payload from geometry you already have.

Full measurement record, with every count reproducible from your tree:
`Step10_docs/impl/2026-09-08_openubem-3d-export-layouts-audit.md`.
