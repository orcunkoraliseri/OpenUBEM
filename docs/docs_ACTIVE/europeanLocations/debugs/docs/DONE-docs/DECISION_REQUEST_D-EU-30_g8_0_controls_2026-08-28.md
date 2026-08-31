# Decision request `D-EU-30` — disposing of the 29 `f>0` cells whose `f=0` control is not perimeter-grade (`G8.0`)

**Date:** 2026-08-28
**Status:** `RULED` (Option A selected)
**Raised by:** manager session, after `D-EU-29` closed `G8.15` and left `G8.0` as the arc's only open item
**Nothing here asks for compute.** Every number below was re-derived by this session from
`docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv` (1,530 rows = 510 cells × 3 replicates),
the artefact already on disk. No simulation, no re-run, no network.

---

## 0. Why this document exists

`EU-09` scores **`G8.0` FAIL 99/121**. The gate's own text is *"all non-zero cells have a successful
matching `f=0` control"* (`openubem/validation/step8_gates.py:187`), and its code criterion is
`control.status == "success"` (`:154`). Of the **121** `f>0` cells inside the `D-EU-28` perimeter of 149,
**99 clear that criterion and 22 do not** — hence the score.

But the criterion the gate applies is *weaker than the perimeter's own certification rule*. `D-EU-28`
admits a cell only if it is `completed` **and** `severe_count = 0` **and** `fatal_count = 0` **and**
marker-free **and** bitwise-identical in `heating_kwh` across three replicates. Applying that same
standard to the controls gives a second, larger number: **29 of the 121 `f>0` cells have an `f=0` control
that is not itself perimeter-grade.**

🔴 **The question is not how to make `G8.0` pass.** It is which of the two standards governs an
`f`-versus-baseline claim, and what happens to the cells that fail it. That is an owner ruling, not a
measurement.

---

## 1. What is actually there, re-derived this session

| population | count |
|---|---:|
| perimeter cells (`D-EU-28`) | **149** (`uk` 75, `it` 74, `es` 0) |
| of those, `f > 0` | **121** |
| `f>0` cells whose `f=0` control **completed in all three replicates** | **99** — the gate's own 99/121 |
| `f>0` cells whose `f=0` control is **perimeter-grade** | **92** (`it` 47, `uk` 45) |
| `f>0` cells with **no matching `f=0` control row at all** | **0** |

The 29 that fail the stricter standard split into two disjoint groups, and they are **not the same kind
of defect**:

**Group I — 22 cells, control has a failed replicate.** The `f=0` control ran three times and one run
returned `ENGINE_FAILED`. Eight archetypes, both folds (`it` 11 cells, `uk` 11):

| fold / archetype | `f>0` cells | control replicate statuses |
|---|---:|---|
| `it` `IT.MidClim.AB.04.Gen.ReEx.001.001` | 1 | `COMPLETED, COMPLETED, ENGINE_FAILED` |
| `it` `IT.MidClim.MFH-AB.07.Gen.ReEx.001.001` | 3 | `ENGINE_FAILED, COMPLETED, COMPLETED` |
| `it` `IT.MidClim.TH.02.Gen.ReEx.001.001` | 3 | `ENGINE_FAILED, COMPLETED, COMPLETED` |
| `it` `IT.MidClim.TH.03.Gen.ReEx.001.001` | 4 | `ENGINE_FAILED, COMPLETED, COMPLETED` |
| `uk` `GB.ENG.MFH.07.Gen.ReEx.001.001` | 2 | `COMPLETED, COMPLETED, ENGINE_FAILED` |
| `uk` `GB.ENG.MFH.08.Gen.ReEx.001.001` | 4 | `COMPLETED, COMPLETED, ENGINE_FAILED` |
| `uk` `GB.ENG.TH.02.Gen.ReEx.001.001` | 2 | `COMPLETED, COMPLETED, ENGINE_FAILED` |
| `uk` `GB.ENG.TH.04.Gen.ReEx.001.001` | 3 | `COMPLETED, ENGINE_FAILED, COMPLETED` |

⚪ Every one of these controls **did produce a heating value on two of three runs**. What is missing is
the third, i.e. the reproducibility evidence — not the number.

**Group II — 7 cells, control completed cleanly three times and is not reproducible.** Three archetypes:

| fold / archetype | `f>0` cells | control: replicates | severe | markers | distinct `heating_kwh` |
|---|---:|---|---:|---|---:|
| `it` `IT.MidClim.MFH-AB.08.Gen.ReEx.001.001` | 1 | 3/3 `COMPLETED` | 0 | none | **2** |
| `uk` `GB.ENG.TH.01.Gen.ReEx.001.001` | 3 | 3/3 `COMPLETED` | 0 | none | **2** |
| `uk` `GB.ENG.TH.08.Gen.ReEx.001.001` | 3 | 3/3 `COMPLETED` | 0 | none | **2** |

🔴 **Group II is `FINDING 181` appearing inside the perimeter's own control set.** These three controls
exit 0, emit no Severe, carry no marker, and still return two different annual heating values from three
identical runs. They are exactly the failure mode `FINDING 181` describes, and they are the reason the
gate's `status == "success"` test is not sufficient: **`completed: true` is necessary and not sufficient**
is already this arc's standing lesson, and here it is the *control* that fails it.

⚪ At archetype level: **39 archetypes hold at least one certified `f>0` cell; 28 of them hold a
perimeter-grade `f=0` control and 11 do not** (8 in Group I, 3 in Group II).

---

## 2. What this does and does not touch

⚪ **It does not move `it` 108.25 kWh/m².** That figure is a *level*, area-pooled over the certified `it`
cells; it never subtracts a control. `EU-10`'s dossier is unaffected by any option below.

⚪ **It does not touch the 15 five-`f` pairs** (`uk` 8, `it` 7). A five-`f` archetype is certified at all
five levels *including* `f=0` by construction, so every one of the 15 already has a perimeter-grade
control. The `FINDING 184` sensitivity result stands whichever option is chosen.

⚪ **It does not reopen `FINDING 184`.** The `f` manipulation is mean-conserving by construction
(`openubem/semantic/european_schedules.py:56`, asserted at `:60`). **No option here makes an annual
figure quotable.** Peak and timing claims only.

🔴 **What it does decide** is the denominator of every `f`-versus-baseline statement the arc may ever
publish: **121, 99 or 92.**

---

## 3. Options

- [x] **A — Adopt the strict standard: the `f`-difference perimeter is 92 cells / 28 archetypes.** *(adopted)*
  A cell may enter an `f`-versus-baseline claim only if its `f=0` control is itself perimeter-grade under
  `D-EU-28`. The 29 are **excluded by ruling, not repaired**. `G8.0` is recorded as **FAIL 99/121,
  carried with a stated exclusion of 29** — the gate is *not* marked PASS, because the standard that
  excludes the 29 is stricter than the gate's own and passing it would be an inconsistency in the other
  direction. No compute, no re-run, nothing on disk changes, and the single agreed re-run stays intact
  for `FINDING 181`.
  **Price:** the arc publishes a difference perimeter (92) that is smaller than its level perimeter (149),
  and every `f`-difference statement must carry both numbers.

- [ ] **B — Spend the single agreed re-run on the 11 controls.**
  Re-run the 8 Group I `f=0` controls (to replace the `ENGINE_FAILED` replicate) and the 3 Group II
  controls (to see whether the non-reproducibility survives), and re-score. Best case recovers up to 29
  cells and takes the difference perimeter to 121.
  **Price:** 🔴 the re-run budget is **SPENT** — one re-run, not one per ruling — and `FINDING 181` has
  the prior claim on it. Group II *is* `FINDING 181`, so this option partly overlaps that claim; Group I
  does not. It also cannot be scoped without GSSCanada 4J.

- [ ] **C — Accept the gate's own criterion: the difference perimeter is 99, and `G8.0` reads PASS 99/121
  after the 22 are excluded.**
  Treat `completed` as the control standard, exclude only Group I, and admit Group II's 7 cells.
  **Price:** 🔴 it admits seven cells whose baseline is demonstrably not reproducible, against this arc's
  own standing lesson. It buys the gate rather than passing it, and it would be the first place in the
  arc where `completed: true` alone was accepted as sufficient.

- [ ] **D — Declare `G8.0` VACUOUS or not applicable.** Refused on sight and listed only for completeness:
  121 of 149 perimeter cells are `f>0` with a matching control row, so the population is neither empty nor
  single-valued.

- [ ] **E — Other** (state it below).

> **Ruling:** Option A adopted. Adopt the strict certification standard: the f-versus-baseline difference perimeter is 92 cells across 28 archetypes (it 47, uk 45). The 29 f>0 cells whose f=0 control is not perimeter-grade (22 in Group I, 7 in Group II) are excluded by ruling from any difference claims. G8.0 is recorded as FAIL 99/121 carried with a stated exclusion of 29. No re-run compute is spent, preserving the single agreed re-run budget for FINDING 181.
>
> **Owner name / initials:** Project Lead / Evaluator (AUTHOR / O.I.)  **Date:** 2026-08-28

---

## 4. What must be written if `A` is ruled

1. `STATE_european_locations_v2.md` §1 gains one bar: **no `f`-versus-baseline difference may be quoted
   for the 29 excluded cells; the difference perimeter is 92 cells / 28 archetypes, against a level
   perimeter of 149.**
2. §3 records `G8.0` as **FAIL carried with a stated exclusion**, and the arc's open-item list becomes
   `FINDING 181` only.
3. `EU-09` stays *In progress* — its acceptance requires every gate scored, and a carried FAIL is scored,
   not cleared. **`G8.0` must never be reported as PASS on the strength of this ruling.**
4. The progress log gains one row; the director prompt gains one section.

---

## 5. Evidence

| claim | where |
|---|---|
| perimeter = 149 (`uk` 75, `it` 74, `es` 0), `f>0` = 121 | `docs/docs_ACTIVE/europeanLocations/outputs/deu27_rerun_cells.csv`, re-derived this session |
| gate text and the `status == "success"` criterion | `openubem/validation/step8_gates.py:151-154`, `:187` |
| 99 controls `completed` 3/3; 92 perimeter-grade; 0 controls missing | same CSV, same derivation |
| Group I — 22 cells / 8 archetypes, one `ENGINE_FAILED` replicate each | same CSV, `completion_status` column |
| Group II — 7 cells / 3 archetypes, clean 3/3 with two distinct `heating_kwh` | same CSV, `heating_kwh` column |
| `G8.0` FAIL 99/121 as scored by GSSCanada 4J | `previous/MVP_european_locations.md` §9.7.3 EU-09/EU-10 addendum |
| the certification rule and the `D-EU-28` Option B ruling | `previous/MVP_european_locations.md` (Arc status), `implementation/PLAN_deu27-timestep12-rerun-2026-08-28.md` — `D-EU-28` has no standalone request document |
| `completed: true` is necessary and not sufficient | `FINDING 181`, `previous/MVP_european_locations.md` |
