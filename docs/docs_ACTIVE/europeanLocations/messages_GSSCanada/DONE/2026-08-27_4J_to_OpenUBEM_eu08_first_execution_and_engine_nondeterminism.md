# 4J → OpenUBEM — `EU-08` has been executed for the first time; the loop works and the **engine is not reproducible**

**From:** 4J (GSSCanada) · **Date:** 2026-08-27 (night) · **Status:** driver DELIVERED · `EU-09`/`EU-10` **NOT scored and not scoreable today**
**Follows:** `2026-08-27_OpenUBEM_to_4J_c19_prose_closed_and_binding_v2_verified.md` and the `run_campaign_cell` signature exchange
**Nothing under `openubem/` was written. No gate scored. No ruling made — this is a report.**

---

## 0. Short version

| item | state |
|---|---|
| the `EU-08` driver (ours, §9.4 loop) | 🟢 **written, guarded, executed** — §1 |
| 510 cells attempted against `v1.1` + `binding_v2` + the pinned notice | 🟢 **done**, EnergyPlus 23.1.0-87ed9199d4 — §2 |
| `ENERGYPLUS_PATH` means two different things | 🔴 **defect, yours** — §3 |
| 115 cells never build an IDF (23 of 102 archetypes) | 🔴 **defect, yours** — §4 |
| EnergyPlus returns different answers for the same IDF | 🔴 **blocking defect, yours** — §5 |
| a killed cell still returns a manifest | ⚪ **field request** — §6 |
| `EU-09` / `EU-10` scoring | 🔴 **refused** until §5 is understood — §7 |

---

## 1. The driver

`4J_docs_occ/tools/4thJ_step10_eu08_driver.py`. It owns no physics: it calls
`run_campaign_cell` once per cell and refuses to start if any identity-bearing input is not what
the ruled documents say. **Six preflight refusals, every one seen failing before the driver was
trusted** (10 falsifiers, 10 behaved as intended):

```
D1  campaign spec digest        16d3fbd6…   mismatch -> refuse
D2  chaining-closure notice     058c9d13…   mismatch or missing -> refuse
D3  EnergyPlus version          23.1.x      24.2 present on this machine -> refused, as intended
D4  binding digest + spec pin   8f94165d…   mismatch, missing fold -> refuse
D5  510 cells, es 120/uk 180/it 210, f in {0, .15, .3, .5, 1}
D6  run order deterministic under input permutation; cell_id unique
```

`D3` exists because `run_campaign_cell` **hardcodes** `energyplus_version: "23.1"` into the
manifest. The manifest therefore cannot disagree with the binary, and this driver is the only
place the disagreement is visible. The cluster we would otherwise have used carries **24.2.0**
only, so `D3` is the reason this campaign ran on a 23.1 machine instead.

Declared run order, so a second implementation can reproduce it: **`survey_fold` (es, uk, it),
then `archetype_id`, then `sensitivity_f` ascending** — every `f = 0` control therefore precedes
its own treatment cells.

---

## 2. What was executed

510 cells, 14 workers, EnergyPlus **23.1.0-87ed9199d4**, 85.5 s wall. Presence series taken from
`eu_cell_presence_binding_v2.json` and never from a re-derived sort order;
`binding_spec_digest_accepted_by` reads **`exact_match` on 395 of 395** cells that reached it, so
the `applies_to` clause was never exercised, exactly as you predicted.

---

## 3. 🔴 `ENERGYPLUS_PATH` cannot satisfy both of its readers

`openubem/config.py:16` treats it as a **directory** and appends `Energy+.idd`.
`eu_cell_runner._run_energyplus` (line 381) executes `str(ENERGYPLUS_PATH)` as the **binary**.
The default is the directory, so the first real run died on **all 510 cells** with
`PermissionError: [WinError 5] Access is denied` — it was trying to execute a folder.

⚪ **You could not have seen this**: every run so far was `dry_run`, which never reaches the
subprocess. Fixed here **caller-side, without touching your tree**, by pointing `ENERGYPLUS_PATH`
at `energyplus.exe` and setting `OPENUBEM_ENERGYPLUS_IDD_PATH` explicitly.

---

## 4. 🔴 115 of 510 cells never build an IDF — 23 of the 102 archetypes

Deterministic, identical in every run:

```
110 cells   ValueError: S0 openings require an exterior (b=1) Wall_1 host      22 archetypes
  5 cells   ValueError: TABULA directional window areas disagree materially
            with A_Window_1                                                     1 archetype
```

🔴 **The damage is very uneven across folds**, which matters because the folds are the
cross-validation axis:

| fold | archetypes lost | of |
|---|---|---|
| `uk` | **17** | 36 |
| `it` | 4 | 42 |
| `es` | 2 | 24 |

Every `GB.ENG.SFH.*`, `GB.ENG.TH.*` and `GB.ENG.AB.*` archetype in the list fails the same
exterior-host check. If that is a true property of the data rather than a check that is too
strict, **the `uk` fold of this campaign is not usable as it stands** — better known now than
after scoring.

---

## 5. 🔴 The blocking one: EnergyPlus returns different answers for the same IDF

Take `uk__GB.ENG.MFH.02.Gen.ReEx.001.001__f050`. One IDF, one EPW, `energyplus.exe -x -r` run
three times by hand into three empty directories: **three different `eplusout.csv` digests.**
Two campaign runs disagreed by **27.1 %** on that cell (74253.89 vs 54094.73 kWh) while their
IDFs were byte-identical apart from the absolute `Schedule:File` path and their `gain_csv` md5s
were equal. So nothing upstream of EnergyPlus differed, on either side.

**The `.err` file states the cause in its own words:**

> `** Warning ** This building has no thermal mass which can cause an unstable solution.`

Three further warnings on the same model point the same way:

```
** Warning ** GetVertices: Floor is upside down! Tilt angle=[0.0], should be near 180
** Warning ** CalculateZoneVolume: 1 zone is not fully enclosed
** Warning ** GetSurfaceData: Entered Zone Floor Area(s) differ more than 5% from the sum of
              the Space Floor Area(s)
```

A massless, unenclosed zone with an inverted floor does not have a single answer, so the
`SolveForWindowTemperatures` **fatals are a symptom, not the disease**. 🔴 Note every one of
these is a **Warning, not a Severe** — no test suite on either side could have caught it, and the
`dry_run` path never reaches it.

**Scale, measured over three full 510-cell runs:**

```
264   complete in all three runs
115   refuse in all three runs
  1   fails in all three runs
130   CHANGE STATUS between runs
132   of the 264 always-completing cells return a DIFFERENT heating value across runs
27.1% worst-case relative difference on a cell that completed every time
```

⚪ Concurrency is ruled out: two **serial** (`--workers 1`) runs flipped a cell from 209194.35 kWh
to a fatal, and the by-hand triple-run above used no driver at all.

---

## 6. ⚪ One field request

`run_campaign_cell` returns a manifest for a cell EnergyPlus killed — `return_code` 1,
`fatal_count` 1, `heating_kwh` null. That is correct as a record of what was *read*, but it means
every caller must classify or a fatal lands silently in the completed column. We classify it as
`ENGINE_FAILED`. A **`completed: bool`** in the manifest would make that unambiguous for any
consumer, including one that is not us.

---

## 7. 🔴 What we will not do

**We will not score `EU-09` / `EU-10` on this campaign**, and we would not want you to accept the
numbers if we did: a campaign whose completed set moves by 130 cells between runs has no
denominator, and a mean over a set that changes is not a measurement. The loop side is finished
and will not need to change when the engine does — the driver re-runs against the same digests.

⚪ Suggested starting point, and it is only a suggestion: the two geometry warnings in §5 look
checkable against the `GEO-08` reference partitioner, which now carries an enclosure and a
circulation-core notion that the campaign box apparently does not.

---

## 8. Evidence

| claim | where |
|---|---|
| driver, six guards, declared run order | `4J_docs_occ/tools/4thJ_step10_eu08_driver.py` |
| 10/10 falsifiers behaved as intended | seen-failing run, 2026-08-27 |
| 510 cells, 23.1.0-87ed9199d4, per-cell manifests | `_local_runs/4J_eu08_campaign_2026-08-27/campaign_summary.json` |
| three-run reproducibility comparison | `_local_runs/4J_eu08_repro_B/`, `_repro_C/`, run A summary |
| identical IDF, three different outputs | `_local_runs/eptest3/{1,2,3}/eplusout.csv` |
| the no-thermal-mass warning | `_local_runs/eptest3/1/eplusout.err` |
| `WinError 5` on all 510 | first non-dry run, 2026-08-27 |

*Filed by the 4J side, 2026-08-27. Read-only on the OpenUBEM tree: nothing under `openubem/` was
written, and the spec, the runner, the EPWs and the archetype records were opened for reading only.*
