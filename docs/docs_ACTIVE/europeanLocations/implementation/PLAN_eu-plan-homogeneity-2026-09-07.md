# PLAN — balance the dwelling cut, re-plan and re-simulate the affected buildings only (`eu-plan-homogeneity-2026-09-07`)

**Slug:** `eu-plan-homogeneity-2026-09-07`. **Opened 2026-09-07.** Governing rule documents (read-only):
`rules/RULES_dwelling_layout_scheme_nocore_2026-09-03.html` (`D-EU-79`, `D-EU-80`, the seven checks) and
`rules/RULES_dwelling_layout_groups_nocore_2026-09-03.html` (the eleven group rules). Prior state:
`STATE_european_locations_v5.md` `FINDING 244` (§3) and `FINDING 258` (§8, 2026-09-07).

**Context.** The owner opened `plans3D/PLANS_FR-LYO-HAUTCOEURPENTES_nocore_2026-09-03_r5.html`, building
`BATIMENT0000000240880367_part0` (complex multi-wing, `k = 4`, 8 storeys, 784 m² footprint): three thin
strip dwellings `D1`–`D3` stacked at one end of one wing, and `D4` swallowing both remaining wings. The
plate is certified `PASS ALL 7 CHECKS`. Its stored area spread (`min/max`) is **0.0527 — a 19 : 1 ratio**.

**Owner ruling 2026-09-07 (verbatim):** *"based on the global rules […] we are aiming homogeneous floor
planning, but there are some flaws […] please scan similar buildings, re-plan floor plans and re-simulate."*
Registered as **`D-EU-107`**. It supersedes nothing in `D-EU-105`'s "per affected building only" clause —
it *scopes* it: the affected set is defined by measurement (T01), and only that set is re-cut, re-emitted
and re-simulated. **No full-batch re-cut, no full-fleet re-simulation.**

**The flaw is already diagnosed, and is not new.** `FINDING 244` (2026-09-03) named the mechanism and even
proposed the remedy — *"an area balance gate (e.g. `C12`, max/min ratio ≤ 2.0) and multi-wing/grid cutting
for non-convex morphologies"*. It was never implemented. `FINDING 258` is the same defect seen again by the
owner on a Lyon plate. This plan implements `FINDING 244`'s own remedy.

**Root cause, cited, two parts:**
1. **Nothing scores balance.** `_plate_score` (`openubem/geometry/european_nocore.py:1038-1069`; bench twin
   `scripts/eu21/07_nocore_tests.py`) ranks candidates on coverage, `C5`, `C6`, `C4`, `C11`, `-pinch`,
   `min C6`, `-max aspect`. **No term reads flat area.** Two candidates that both pass are separated by
   pinch and aspect only, so a 19 : 1 split can win over a balanced one.
2. **Leftover absorption donates a whole wing.** `donate_leftovers` (`european_nocore.py:416`, bench
   `07_nocore_tests.py:314`, rule `D-EU-80`) folds every orphan fragment into "the flat it touches most".
   On a multi-wing plate a parallel column cut orphans entire wings (`C4` forbids the MultiPolygon, so
   `_seed_flats` keeps only the largest piece), and the whole wing is then donated intact to one flat.

**The metric already exists** — do not invent one. `07_nocore_tests.py:1652` already computes and stores
`spread = round(min(areas)/max(areas), 4)` on every plate of every district census. It is reported in the
sheets (`:1776`, `:1941-1955`) and has never been a gate.

---

## 2. Hard rules for the executor

1. **Never widen, loosen, or re-calibrate an existing check.** `C1`, `C3`, `C4`, `C5`, `C6`, `C10`, `C11`
   and `MAX_FLAT_ASPECT = 2.5` are frozen (`D-EU-82`, `D-EU-87`, `D-EU-89` clause 2). The balance work adds
   a term; it never buys balance by relaxing another check.
2. **Bench first, engine second, parity proven.** Every cutter change lands in
   `scripts/eu21/07_nocore_tests.py` first, is measured on the 550-plate bench and the four district
   censuses, and is then **copied** (never re-implemented) into `openubem/geometry/european_nocore.py`.
   Acceptance is `scripts/eu21/09_engine_parity.py` reporting **0 mismatches** on all 2,529 compared plates
   — the same gate `CP-1` of the carry-in plan used (`implementation/DONE/PLAN_eu-engine-nocore-carryin-2026-09-03.md`).
3. **No-regression is a hard gate, not a report.** A building that passed all seven checks before must pass
   all seven after. Any plate moving `PASS → FAIL` stops the task; report it, do not "accept the trade".
4. **Only the affected set is re-cut, re-emitted and re-simulated** (`D-EU-105`, `D-EU-107`). Every
   unaffected building's emitted IDF must come back **`idf_sha256`-identical** (T04's gate). If unaffected
   IDFs move, the change is wrong — stop.
5. Re-emission writes to a **new dated folder**; never overwrite
   `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_ceiling82_2026-09-05/`, which is the published campaign.
6. **Cluster work is director-only.** The executor never runs `sbatch`, `ssh`, `srun` or any Speed command
   (T05/T06 are marked director-only below).
7. No EnergyPlus run beyond the local sample battery T04 calls for. No network fetch.
8. No code comments; no new files outside §3.

---

## 3. File layout (only these may be touched)

Code:
- `scripts/eu21/07_nocore_tests.py` — bench cutter + `C12` (T02)
- `openubem/geometry/european_nocore.py` — the engine copy of the same change (T03)
- `tests/test_eu21_area_balance.py` — new unit tests (T02)

Evidence written (new):
- `openubem/outputs/eu_evidence/EU-21/homogeneity/affected_buildings_2026-09-07.csv` (T01)
- `openubem/outputs/eu_evidence/EU-21/homogeneity/spread_before_after_2026-09-07.csv` (T02)
- `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_balance_2026-09-07/` — re-emitted IDFs, affected only (T04)

Read-only, cited never edited: `rules/*.html`, `plans3D/PLANS_*.html`,
`openubem/outputs/eu_evidence/EU-21/district_plans/*_r5.json`,
`openubem/outputs/eu_evidence/EU-11/*_ceiling82_2026-09-05/**`.

Doc: `docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-plan-homogeneity-2026-09-07.md` — §8 only.

---

## 4. Dependency decisions (pinned)

- **Metric:** `spread = min(flat area) / max(flat area)` per plate, per storey-plate — the existing field
  (`07_nocore_tests.py:1652`). Do not switch to a coefficient of variation, a Gini, or a per-dwelling
  target area; the arc's whole evidence trail is in `spread`.
- **Gate:** `C12` passes when `spread >= 0.50` (max/min ≤ 2.0 : 1), the ratio `FINDING 244` itself
  proposed. `k <= 1` plates are **not evaluated** — the same exemption `D-EU-93` gave `C11`, for the same
  reason (nothing was cut, so there is nothing to compare).
- **`C12` is scored, then gated, in that order** (T02a → T02b), so the effect of each half is measured
  separately. It is check number **twelve**; do not renumber or reuse `C7`/`C8`/`C9`.
- **Director's ruling on the "aimed for" area:** homogeneity here means *dwellings on one plate resemble
  each other*, never *dwellings match a target m²*. No absolute area target enters this plan.
- No new dependency; `shapely` only, as now.

---

## 5. Measurement of record (director, 2026-09-07 — the executor re-derives, does not trust)

Computed from the four `_r5` district censuses, `status != ERROR`, `drawn_per_floor >= 2`:

*Corrected 2026-09-07 (director, after T01): the `IT-BOL-GALVANI2` `< 0.33` cell read 92 and the
fleet `< 0.33` total read 149; the true counts on the stored rounded `spread` field are **89** and **146**.
The affected set (`< 0.50`) and the simulated overlap are unchanged.*

| District | plates | `k >= 2` | `spread < 0.50` | `< 0.33` | `< 0.25` | also in the simulated ceiling82 population |
|---|---|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | 1,194 | 663 | **123** | 52 | 30 | 121 |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 171 | **16** | 4 | 4 | 15 |
| `GB-LDN-STDUNSTANS` | 1,242 | 66 | **3** | 1 | 1 | 3 |
| `IT-BOL-GALVANI2` | 1,220 | 910 | **202** | 89 | 63 | 201 |
| **fleet** | **4,186** | **1,810** | **344** (19.0 % of `k >= 2`) | 146 | 98 | **340** |

So the re-simulation set is **≈340 buildings**, not 3,344 — **10.2 % of the campaign**, which is what makes
`D-EU-105`'s "not all batch, for some" achievable as stated.

⚠ The `idf_state` field inside the `_r5` JSONs is **stale** (written 2026-09-03, before the engine carry-in
and before the ceiling82 re-prep). Never use it to decide what was simulated. The simulated population is
`openubem/outputs/eu_evidence/EU-11/<DISTRICT>_ceiling82_2026-09-05/prepared_buildings.csv`.

---

## 5b. All four districts, per district (director, 2026-09-07 — owner asked whether this is district-specific)

**It is not.** All four carry imbalanced plates before the fix. The rate tracks morphology: the two
large-block districts (Bologna, Madrid) are worst, the terrace-row district (London) is nearly clean and is
the only one the `D-EU-107 f` scoring fix takes to zero.

| District | plates with `k >= 2` | imbalanced (`spread < 0.50`) | share | in the simulated population | after `D-EU-107 f` (census `< 0.50`) |
|---|---|---|---|---|---|
| `ES-MAD-BERRUGUETE` | 663 | **123** | 18.6 % | 121 | 26 |
| `FR-LYO-HAUTCOEURPENTES` | 171 | **16** | 9.4 % | 15 | 3 |
| `GB-LDN-STDUNSTANS` | 66 | **3** | 4.5 % | 3 | **0** |
| `IT-BOL-GALVANI2` | 910 | **202** | 22.2 % | 201 | 40 |
| **fleet** | **1,810** | **344** | **19.0 %** | **340** | **69** |

⚠ The last column is the census `spread < 0.50` count over all `k >= 2` plates, which is the executor's own
before/after measurement basis; the frozen affected set (column 3) was cut on the same field but pinned at
T01, so the two columns differ by one or two plates per district for the reasons already corrected in §5.
Quote column 3 for scope and the last column for effect; never mix them in one sentence.

**No district is presentable on this plan alone.** Even `GB-LDN-STDUNSTANS`, which reaches `0` imbalanced
plates, still has 49 buildings emitted as single-zone massing under `D-EU-109` (`FINDING 262`) and only 451
of 1,242 buildings simulated before `D-EU-108`'s recovery. A district is finished when all three plans have
landed on it, not when this one has.

**The overlap that fixes the ordering:** 232 of the 344 affected plates are also `D-EU-109`-undivided
(`ES-MAD` 88, `FR-LYO` 9, `GB-LDN` 1, `IT-BOL` 134), and all 232 are recoverable. Their imbalance is not
expressed by any IDF in the current fleet, so no `C12` improvement may be claimed from a pre-`D-EU-109`
emission.

---

## 6. Tasks

### T01 — Scan: freeze the affected set

**What:** one CSV listing every building whose cut is imbalanced, with the evidence for it.
**Why:** everything downstream (re-cut, re-emit, re-simulate, EUI restatement) is scoped by this list; it
must be frozen and citable before any code changes.
**How:** read the four `_r5` district JSONs; for every plate with `status != "ERROR"` and
`drawn_per_floor >= 2`, emit `building_id, district, group, k, storeys, area_m2, spread, verdict,
checks_failing, in_ceiling82_population` to
`openubem/outputs/eu_evidence/EU-21/homogeneity/affected_buildings_2026-09-07.csv`, flagged
`affected = spread < 0.50`. Join `in_ceiling82_population` on `building_id` against each district's
`<DISTRICT>_ceiling82_2026-09-05/prepared_buildings.csv`.
**How to test:** reproduce §5's table exactly from your own CSV — same six numbers per district. Report any
cell that differs rather than adjusting the table. Also report, per district, the group breakdown of the
affected set and the ten worst `spread` values with their `building_id`.

### T02 — `C12`: score balance, then gate it (bench only)

**T02a (scored):** add `spread` as a ranking term to the bench cutter's `_plate_score` twin, ranked **after**
the hard gates (coverage, `C5`, `C6`, `C4`, `C11`) and **before** `-pinch`/`-max_aspect`, so a balanced
candidate wins among candidates that already pass everything. Re-run the 550-plate bench and all four
district censuses. Report: `PASS`/`FAIL` per check before vs after (must be **0 regressions**), and the
`spread` distribution before vs after (`min`, median, count `< 0.50`, `< 0.33`, `< 0.25`) to
`spread_before_after_2026-09-07.csv`.

**Director's ruling 2026-09-07 (`D-EU-107 f`) — correction to the T02a spec above, after the T02a
fleet measurement.** The T02a text names the hard gates as "coverage, `C5`, `C6`, `C4`, `C11`" and omits
**`C10`**. That omission is a drafting error in this plan, not an executor deviation. `C10`
(`pinch_total <= 0.10 m²`, `run_checks` `:1765`) is one of the seven frozen checks, but it enters
`_plate_score` only as the *continuous* term `-pinch_total`; ranking `spread` above it therefore lets a
balanced candidate outrank a `C10`-passing one, which the T02a run measured as **458 `PASS` → `FAIL`
verdict flips, all on `C10` alone** (550-bench 78, `ES-MAD` 140, `FR-LYO` 33, `GB-LDN` 16, `IT-BOL` 191).
That is hard rule 3, so the measured outcome is rejected and the spec is corrected here.

**Corrected tuple order** — booleanise `C10` and rank it with the other hard gates, keeping the
continuous term where it is as the tie-break, exactly the pattern `C6` (`c6_ok` then `min_c6`) and `C11`
(`c11_ok` then `-max_aspect`) already use in this same function:

`(cov_ok, c5_ok, c6_ok, c4_ok, c11_ok, c10_ok, spread, -pinch_total, min_c6, -max_aspect)`
with `c10_ok = (pinch_total <= 0.10)`, the frozen constant, never a widened allowance.

This is `PASS`/`FAIL`-preserving on `C10` by construction: a `C10`-passing candidate now beats a
`C10`-failing one on the boolean before `spread` is ever consulted, so no verdict can flip. `spread` keeps
its full T02a intent — it still chooses the more balanced candidate among those already tied on every one
of the seven checks. Among candidates that all *fail* `C10`, `spread` may now pick a larger residual pinch
than the pre-T02a order would have; that changes no verdict and is accepted, but the executor reports the
`C10` pinch-magnitude distribution before vs after alongside the verdicts so the effect is on record.

`_fully_ok` (`:1093`) unpacks this tuple by position and must be updated with it.

**T02b (gated + cut repair):** add `C12` to the printed check set (`spread >= 0.50`, not evaluated at
`k <= 1`), and add the two cut repairs `FINDING 244` names, in this order, each measured on its own:
1. **Per-wing allocation for non-convex plates:** where `lobes_of`/wing decomposition finds ≥ 2 wings,
   allocate `k` across wings proportionally to wing area (largest remainder), then cut each wing
   independently, instead of slicing columns across all wings at once.
2. **Bounded donation:** in `donate_leftovers`, a leftover piece whose area exceeds **0.5 ×** the current
   mean flat area is not donated whole — it is re-cut against the receiving flat so the pair ends balanced;
   if no such split clears `C4`/`C5`/`C6`/`C10`/`C11`, the donation falls back to today's behaviour and the
   plate is reported `C12 FAIL`, honestly, never forced.

**Why:** (1) is the mechanism that creates the orphan wing; (2) is the mechanism that dumps it into one flat.
Fixing only one leaves the defect.
**How to test:** unit tests in `tests/test_eu21_area_balance.py` covering: the `k <= 1` exemption; a plate
whose donation is bounded; a two-wing plate allocated 2 + 2; a plate where no balanced split clears the
other checks (must report `C12 FAIL`, not force a cut). Then the full 550-plate bench + four censuses:
**0 regressions on C1/C3/C4/C5/C6/C10/C11**, and report how many of T01's 344 now clear `C12`.

### T03 — Carry the change into the engine, prove parity

**What:** copy the T02 change into `openubem/geometry/european_nocore.py`.
**How:** extraction, not re-implementation (`D-EU-95`'s own rule). Then run
`python scripts/eu21/09_engine_parity.py` for all four districts.
**How to test:** **0/0/0/0 mismatches on 2,529 compared plates**, `input_missing = 0`. Anything else stops
the plan.

### T03b — Re-point the parity gate at a current baseline (`D-EU-107 g`)

**What:** regenerate the four district-plan baselines under the corrected bench and re-run parity twice.
**Why:** `_r5` is a 2026-09-03 bench snapshot; T02a intentionally changed the bench, so `_r5` can no
longer be the reference. See the `D-EU-107 g` ruling in §7.
**How:** (1) `08_district_viewer.py --district <D> --tag 2026-09-07_r6` for all four districts, every
other argument identical to the original `_r5` invocation, which must be found and quoted; `_r5` is never
overwritten. (2) add `--baseline-tag` to `09_engine_parity.py`, default `2026-09-03_r5`. (3) run parity
against `2026-09-07_r6` and against the default.
**How to test:** run 1 → `0/0/0/0`, compared 2,529, `input_missing = 0`. Run 2 → exactly `0/0/1101/32`
fleet and `0/0/386/13` · `0/0/112/2` · `0/0/36/1` · `0/0/567/16` per district. Either number off by any
amount stops the plan and is reported, never adjusted away. No engine or bench scoring change is permitted
in this task.

### T04 — Re-emit IDFs, affected buildings only

**What:** rebuild IDFs for T01's affected set into
`openubem/outputs/eu_evidence/EU-11/<DISTRICT>_balance_2026-09-07/`.
**How:** the existing prep path (`scripts/run_eu_s2_district_campaign.py::prepare`), restricted to the
affected `building_id`s; never re-emit the whole district into the new folder.
**How to test, all three required:**
1. For **every unaffected** building of each district, `idf_sha256` in the ceiling82
   `prepared_buildings.csv` is unchanged — prove it by re-emitting a **control sample of 25 unaffected
   buildings per district** into a scratch folder and comparing hashes: 100/100 identical.
2. Local EnergyPlus 23.1.0 on a **16-building sample** of the affected set (4 per district, worst `spread`
   first): 0 fatal, 0 severe.
3. Per-district count of re-emitted IDFs equals the affected count from T01.

### T05 — Re-simulate the affected set on Speed — **director only, executor must not run this**

One `sbatch --array=1-N%32 --time=7-00:00:00`, partition `ps`, all four districts submitted in parallel as
separate arrays (~340 tasks total). Packaging follows `scripts/cluster/ship_eu11_fleet.sh`.

### T06 — Harvest, restate the four district EUIs — **director only**

Harvest with a `harvest_eu11_ceiling82_final.py`-shaped merge, precedence **balance-2026-09-07 overrides
ceiling82** for the re-run stems only. Report, per district: pooled EUI before, pooled EUI after, delta in
kWh/m² and %, and the count of stems replaced. 🔴 The four published EUIs (London 97.081151, Lyon 65.935928,
Madrid 77.153998, Bologna 54.935569 kWh/m²) **become stale the moment this lands** — no district EUI may be
quoted between T05 submission and T06's restatement.

### T07 — Republish and record

Regenerate the four `outputs_3D` viewers and the affected buildings' plan pages; update `STATE` §3/§7/§8,
`CHECKLIST` and `BRIEF` §2; register the outcome as `FINDING 260` if any measured behaviour differs from
this plan's predictions; close `FINDING 258` only if the affected set is empty at `spread >= 0.50`.

---

## 7. Stop-and-report points

- **`CP-1` — after T01.** The frozen affected set + §5 reproduction. Director signs the 0.50 threshold
  against the measured tiers before any code is touched.
  **SIGNED 2026-09-07 (owner, verbatim "yes"; director countersigned).** `C12 = spread >= 0.50`
  (`max/min <= 2.0`, `FINDING 244`'s own number), not evaluated at `k <= 1`. Affected set frozen at
  **344 plates** (`affected_buildings_2026-09-07.csv`, 1,810 rows), **340** of them in the simulated
  ceiling82 populations. T01's one reported §5 mismatch was re-derived by the director and the doc was
  corrected in the executor's favour (see §5 note); no other cell moved. T02 is released.
- **`CP-2` — after T02b.** Bench result: 0 regressions on the seven checks, and the `C12` recovery count.
  Director signs before the engine is touched.
**`CP-2` SIGNED — director, 2026-09-07, on the corrected `D-EU-107 f` tuple order.** Gate met as written:
**0 `PASS` → `FAIL` regressions** on all seven checks across the 550-plate bench and all four district
censuses, with the `C10`-failing population identical plate-for-plate before and after. `C12` recovery:
**275 of the 344 affected plates now clear `spread >= 0.50`; 69 still fail**, reported honestly and not
forced, which §6 T02b's own last clause provides for. `tests/test_eu21_area_balance.py` 6 passed / 0 failed.
`spread` `< 0.50` counts: bench `81 → 15`, `ES-MAD` `122 → 26`, `FR-LYO` `17 → 3`, `GB-LDN` `3 → 0`,
`IT-BOL` `199 → 40`.

Three things are on record with this signature, none of them blocking:

1. **The accepted side effect is bounded to plates that already fail `C10`.** Median/max created pinch on
   the `C10`-failing set worsens (bench `2.35 / 7.6 → 5.7 / 21.4 m²`, n=36; `ES-MAD` `1.35 / 34.7 →
   9.7 / 51.7`, n=21; `IT-BOL` `5.9 / 32.8 → 9.0 / 32.8`, n=27). No plate's verdict moves, and `D-EU-107 f`
   predicted exactly this. It must be quoted alongside any `C10` pinch statistic from this arc.
2. **Both T02b cut repairs are contributing nothing measurable.** Repair 1 (per-wing allocation) was already
   in the codebase before this plan (`cut_wingwise`, `FINDING 242`); repair 2 (bounded donation) measured
   inert — identical recovery with it enabled and disabled. So the entire `275` comes from T02a's scoring
   term alone, and the residual `69` is precisely the population the two repairs were written to fix.
   This is diagnosed at **T02c** below before the engine carry, so the carry happens once.
3. 🔴 **`FINDING 262` — the imbalance is mostly invisible today.** **232 of the 344** affected plates
   (`ES-MAD` 88, `FR-LYO` 9, `GB-LDN` 1, `IT-BOL` 134) are also in `D-EU-109`'s 1,524 undivided set: they
   carry a valid imbalanced cut in the census but were rerouted to one zone per floor at emission, so no
   IDF in the current fleet expresses their imbalance. The owner's own exemplar,
   `BATIMENT0000000240880367_part0` (`FR-LYO`, k=4, spread `0.0527`), is one of them. Consequence:
   `D-EU-109` **exposes** this defect rather than being independent of it, which is why the pinned landing
   order (`D-EU-109` → `D-EU-107` → `D-EU-108`) is the only correct one, and why no `C12` improvement can be
   claimed from a pre-`D-EU-109` IDF.

### T02c — Why the two cut repairs are inert (diagnosis, before the engine carry)

**What:** an answer, not a fix: for the 69 plates that still fail `C12`, why does neither repair change the
outcome. **How:** instrument, do not rewrite — count how many of the 69 (a) reach `donate_leftovers` at all,
(b) reach it with a leftover piece above the `0.5 ×` mean-flat-area threshold, (c) attempt a bounded re-cut,
(d) have that re-cut refused by `C4`/`C5`/`C6`/`C10`/`C11`, and which check refuses. Same for repair 1:
how many of the 69 have `>= 2` wings under `lobes_of`/wing decomposition at all.
**How to test:** the counts must sum to 69. Report the dominant path and the dominant refusing check. If
(a) or (b) is near zero the repairs are unreachable, not broken, and that is the answer — say so and stop;
do not widen a threshold to make them fire.

CP-2 is signed and **T02c then T03 are released to a single executor**, in that order, so the engine carry
happens once.

**Director's ruling 2026-09-07 (`D-EU-107 g`) — the parity gate had the wrong reference.**

The T03 executor was right to stop, and its 0/0/1,101/32 is not a regression. `09_engine_parity.py`
(`:46-49`, `:128`) compares the engine against four **frozen** `district_plans/*_nocore_2026-09-03_r5.json`
files. Those were produced by `scripts/eu21/08_district_viewer.py --district <D> --tag 2026-09-03_r5`,
which imports the bench (`M07`, `:38`) — so `_r5` is a *snapshot of the bench as it stood on 2026-09-03*,
before this plan changed `_plate_score`. Running the gate against it tests two claims at once: (i) engine
reproduces bench — what `D-EU-95` intended — and (ii) bench-today reproduces bench-2026-09-03, which this
plan **deliberately falsifies**. A gate that cannot pass unless the plan is abandoned is a mis-specified
gate, not a failed carry. This is my drafting error in T03's "How to test", not an executor deviation.

The gate is **not weakened**: it stays 0/0/0/0 on all four mismatch kinds over 2,529 plates with
`input_missing = 0`. Only its reference moves forward.

**Ruled:**

1. Regenerate the baseline, do not overwrite it. Run `08_district_viewer.py` for all four districts with
   `--tag 2026-09-07_r6`, **every other argument byte-identical to the original `_r5` invocation** (find
   and quote that invocation; if it used `--generic-no-census`, so must this one). The four
   `*_nocore_2026-09-03_r5.json` files are read-only (`D-EU-85`) and stay on disk unchanged as the
   historical record of pre-`D-EU-107` behaviour.
2. Give `09_engine_parity.py` a `--baseline-tag` argument defaulting to `2026-09-03_r5`, so every existing
   invocation and every earlier citation keeps its current meaning. No other change to that harness.
3. Two runs, both required, both reported:
   - `--baseline-tag 2026-09-07_r6` → **must be 0/0/0/0, compared 2,529, `input_missing = 0`.**
   - `--baseline-tag 2026-09-03_r5` (the default) → **must reproduce exactly 0/0/1,101/32 fleet-wide and
     0/0/386/13 · 0/0/112/2 · 0/0/36/1 · 0/0/567/16 per district.**

   The second run is the load-bearing one. Together the two are transitive: if engine ≡ `_r6` exactly, and
   engine vs `_r5` is the same 1,101/32 the pre-regeneration run measured, then `_r6` vs `_r5` is that
   same 1,101/32 — i.e. **the bench and the engine drifted from 2026-09-03 by the identical amount**. That
   is the proof that the drift is `D-EU-107 f`'s intended tie-break reordering and not engine-side
   re-implementation error. Had the engine drifted by a different amount, run 1 would not be 0/0/0/0.
   No separate JSON-diff tool is needed and none may be written.
4. `input_missing = 0` on run 1 is also the population guard: if the `_r6` regeneration silently cut a
   different plate set than `_r5`, parity reports it there rather than hiding it.
5. The `_r6` HTML viewers that `08_district_viewer.py` writes alongside the JSONs are a by-product of the
   regeneration, not a deliverable, and are not published anywhere.

**Accepted from T02c, no action:** the residual 69 is 2 + 27 + 1 + 13 + 26, dominant refusing check `C10`
(8/13), repair 1 structurally inapplicable to 51/69. The 26 "fires but insufficient" bucket the plan did
not anticipate is the largest single cause and is a **capacity** limit of the donation mechanism, not an
unreachability bug — recorded, not fixed under this plan. The T02c instrumentation stays inert
(`_T02C_ACTIVE = False`).

**T03b released.** `CP-3` remains unsigned until both parity runs land as specified above.

**`CP-3` parity half signed — director, 2026-09-07.** Both runs verified by the director directly from
`openubem/outputs/eu_evidence/EU-21/engine_parity/parity_<D>_2026-09-03.json`, not from the executor's report.

- Run A (`--baseline-tag 2026-09-07_r6`): ES-MAD 955, FR-LYO 295, GB-LDN 75, IT-BOL 1204 = **2529 compared,
  0/0/0/0 fleet-wide, `input_missing 0`**. Snapshotted before run B overwrote the files, to
  `openubem/outputs/eu_evidence/EU-21/homogeneity/parity_runA_r6_<D>_2026-09-07.json`.
- Run B (default `2026-09-03_r5`): ES-MAD 0/0/386/13, FR-LYO 0/0/112/2, GB-LDN 0/0/36/1, IT-BOL 0/0/567/16 =
  **0/0/1101/32**, matching `D-EU-107 g` gate 3 exactly. 386+112+36+567 = 1101; 13+2+1+16 = 32.
- Transitivity holds: bench and engine drifted identically off the superseded `_r5` snapshot, so the
  2026-09-03 parity failure was a stale-baseline artefact, not an engine divergence.
- `_r5` immutability re-checked by the director: all four files still carry their 2026-09-03 19:21–19:37
  mtimes and original sizes. Never overwritten.

**The hash half of `CP-3` stays unsigned.** The unaffected-IDF hash proof is produced by `D-EU-109` T03m,
which is still emitting. Nothing from this plan reaches Speed until that lands.

- **`CP-3` — after T03/T04.** Parity 0 mismatches + the unaffected-IDF hash proof. Director signs before
  anything reaches Speed.
- **`CP-4` — after T06.** EUI restatement, director-run, reported to the owner.

---

## 8. Progress log

*(executor appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` +
Artifacts / Deviations / Test status / Notes.)*

#### T01 — Scan: freeze the affected set — completed 2026-09-07

**Artifacts:** `openubem/outputs/eu_evidence/EU-21/homogeneity/affected_buildings_2026-09-07.csv`
(1,810 rows, one per plate with `status != "ERROR"` and `drawn_per_floor >= 2`, all four districts).

**Deviations:** none. `k >= 2` and `drawn_per_floor >= 2` coincide exactly in all four censuses (0
plates with `drawn_per_floor >= 2` and `k < 2`), so the `affected` flag (`spread < 0.50`) needed no
extra `k` gate.

**Test status — §5 reproduction:** 23 of 24 cells match exactly. One mismatch:
`IT-BOL-GALVANI2`, `< 0.33` column — table states **92**, reproduced **89** (verified against the
stored, already-rounded `spread` field; no threshold between 0.330 and 0.339 yields 92, and the
adjacent columns `< 0.50` = 202 and `< 0.25` = 63 both match exactly, so the discrepancy is isolated
to this one cell). Fleet `< 0.33` total is therefore **146**, not 149. Not adjusted in the table per
§6 instruction — reported here for director sign-off.

Reproduced table:

| District | plates | `k>=2` | `spread<0.50` | `<0.33` | `<0.25` | in ceiling82 |
|---|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE | 1,194 | 663 | 123 | 52 | 30 | 121 |
| FR-LYO-HAUTCOEURPENTES | 530 | 171 | 16 | 4 | 4 | 15 |
| GB-LDN-STDUNSTANS | 1,242 | 66 | 3 | 1 | 1 | 3 |
| IT-BOL-GALVANI2 | 1,220 | 910 | 202 | **89** (doc: 92) | 63 | 201 |
| fleet | 4,186 | 1,810 | 344 | **146** (doc: 149) | 98 | 340 |

**Notes:** group breakdown of the 344 affected (spread < 0.50), per district —
ES-MAD-BERRUGUETE: COMPLEX_MULTI_WING 41, COURTYARD 33, U_OR_T_SHAPE 19, SLIVER 8, L_SHAPE 7,
CORRIDOR_RECTANGLE 6, RECTANGLE 6, TRIANGLE 2, TRAPEZOID 1.
FR-LYO-HAUTCOEURPENTES: L_SHAPE 4, COURTYARD 2, U_OR_T_SHAPE 2, COMPLEX_MULTI_WING 2, SLIVER 2,
RECTANGLE 2, SQUARE 1, SLAB 1.
GB-LDN-STDUNSTANS: SLIVER 1, SQUARE 1, U_OR_T_SHAPE 1.
IT-BOL-GALVANI2: COURTYARD 53, COMPLEX_MULTI_WING 52, SLIVER 50, U_OR_T_SHAPE 25, L_SHAPE 13,
TRIANGLE 3, CORRIDOR_RECTANGLE 3, TRAPEZOID 2, RECTANGLE 1.

Worst 10 `spread` values (building_id, district, group, k):
0.0224 `31019` IT-BOL-GALVANI2 COMPLEX_MULTI_WING k=2 ·
0.0266 `28781` IT-BOL-GALVANI2 COURTYARD k=2 ·
0.0281 `32388` IT-BOL-GALVANI2 COMPLEX_MULTI_WING k=3 ·
0.0298 `31610` IT-BOL-GALVANI2 COMPLEX_MULTI_WING k=2 ·
0.0326 `31067` IT-BOL-GALVANI2 COURTYARD k=2 ·
0.0332 `32343` IT-BOL-GALVANI2 SLIVER k=4 ·
0.0343 `32041` IT-BOL-GALVANI2 U_OR_T_SHAPE k=3 ·
0.036 `31431` IT-BOL-GALVANI2 COMPLEX_MULTI_WING k=3 ·
0.0527 `BATIMENT0000000240880367_part0` FR-LYO-HAUTCOEURPENTES COMPLEX_MULTI_WING k=4 (the
owner's original Lyon example, confirmed present in the frozen set) ·
0.055 `31225` IT-BOL-GALVANI2 COMPLEX_MULTI_WING k=2.

#### T02a — C12: score balance (bench only) — completed 2026-09-07, corrected 2026-09-07 (superseded run below)

**First pass (superseded):** `_plate_score` ranked `spread` before the continuous `-pinch_total`
term with no boolean C10 gate in the tuple. Measured fleet-wide as **458 PASS → FAIL
regressions, all on C10** (78/550 bench, 380/1,810 across the four district censuses) — a real
conflict between §6 T02a's literal tuple order and §2 hard rule 3, reported and not accepted.
Superseded by the director's ruling `D-EU-107 f` (§6, 2026-09-07): the omission of a boolean
C10 gate was a drafting error in the plan, not in the T02a edit.

**Corrected artifact:** `_plate_score` (`scripts/eu21/07_nocore_tests.py:1042-1090`) now returns
a 10-tuple `(cov_ok, c5_ok, c6_ok, c4_ok, c11_ok, c10_ok, spread, -pinch_total, min_c6,
-max_aspect)` — `c10_ok = pinch_total <= 0.10` inserted as a hard gate beside C6/C11's own
`*_ok` pattern, `spread` ranked immediately after it, `-pinch_total` kept as the tie-break among
candidates already tied on every gate including C10. `_fully_ok` (`:1093-1102`) updated to the
matching 10-item positional unpack.

**Test status, re-measured against a true pre-T02 baseline (`git show HEAD` of
`07_nocore_tests.py`, loaded as a second module instance, never written to disk under a tracked
path):** 550-bench and all four district censuses (1,810 + 550 plates, same populations as T01
and the first pass) — **0 PASS → FAIL regressions everywhere**, on all seven of
C1/C3/C4/C5/C6/C10/C11: 550-bench C10 514/36 before → 514/36 after (identical); ES-MAD 642/21 →
642/21; FR-LYO 168/3 → 168/3; GB-LDN 63/3 → 63/3; IT-BOL 883/27 → 883/27 — the C10-failing
population is unchanged plate-for-plate in every district. Owner's example plate
`BATIMENT0000000240880367_part0`: `PASS` before and after, spread unchanged at 0.0527, pinch
unchanged at 0.006 m² (this plate's only candidate that clears C10 was already the pre-T02
winner; C12 still `FAIL` for it, see T02b).

**Accepted side effect, on record per the director's ask:** among plates that already failed C10
before (unchanged set, never a new failure), the pinch magnitude worsens, since `spread` still
breaks ties among candidates that all fail the C10 gate. C10-fail `pinch_total` median/max
(before → after): 550-bench 2.345/7.55 → 5.7/21.42 (n=36); ES-MAD 1.345/34.667 → 9.74/51.669
(n=21); FR-LYO 0.433/1.419 → 0.835/19.139 (n=3); GB-LDN 2.069/2.1 → 2.523/3.517 (n=3); IT-BOL
5.928/32.753 → 8.967/32.753 (n=27, max unchanged). Confined entirely to the already-FAIL
population; zero effect on any plate that passes C10.

#### T02b — C12: gate + two cut repairs — completed 2026-09-07, re-measured on the corrected T02a order

**Artifacts unchanged from the first pass** (repair 2's donation-bounding code is independent of
`_plate_score`'s tuple order): `checks["C12"]` in `run_checks` (`:1660-1665` area, `MIN_SPREAD =
0.50` constant), additive only, `rec["verdict"]` still gates on exactly
`("C1","C3","C4","C5","C6","C10","C11")`. `_bounded_split_piece`/`_clears_donation_gates` wired
into `donate_leftovers`, unchanged. Repair 1 (`cut_wingwise`) remains pre-existing
(`FINDING 242`), as reported in the superseded entry — no new code for it either pass.

**Test status:**
- `tests/test_eu21_area_balance.py -q`: **6 passed, 0 failed**, re-run against the corrected
  tuple (the unit tests exercise `run_checks`/`donate_leftovers`/`cut_wingwise` directly, not
  `_plate_score`'s tuple shape, so they were unaffected by the correction and still pass).
- T01's 344 affected plates, honest C12 clearing under the corrected, 0-regression order:
  **275 clear (spread >= 0.50), 69 still C12 FAIL**, no forcing — down from the first pass's
  304/40, because that 304 included candidates the corrected C10 gate now correctly excludes.
- `spread_before_after_2026-09-07.csv` rewritten (`openubem/outputs/eu_evidence/EU-21/homogeneity/`)
  against the true pre-T02 baseline. Per-district spread (before → after): ES-MAD-BERRUGUETE min
  0.0909→0.0928, median 0.9996→0.9999, `<0.50` 122→26, `<0.33` 51→10, `<0.25` 29→5.
  FR-LYO-HAUTCOEURPENTES min 0.0527→0.0527 (unchanged — the owner's plate's own worst value
  survives), median 0.9997→0.9999, `<0.50` 17→3, `<0.33` 4→3, `<0.25` 4→3. GB-LDN-STDUNSTANS min
  0.2021→0.6665, median 0.9996→0.9998, `<0.50` 3→0, `<0.33` 1→0, `<0.25` 1→0. IT-BOL-GALVANI2 min
  0.0224→0.036, median 0.9377→0.9999, `<0.50` 199→40, `<0.33` 86→20, `<0.25` 61→10. 550-plate
  bench: min 0.0891→0.2553, median 0.9997→0.9999, `<0.50` 81→15, `<0.33` 30→1, `<0.25` 16→0.

**Notes:** CP-2 closes clean under the corrected order — 0 regressions on all seven frozen
checks, fleet-wide, confirmed twice (bench + all four censuses). The accepted C10-pinch-magnitude
side effect on the already-failing population is disclosed above per the director's instruction
and is not itself a rule-3 violation (no PASS plate is touched). Reported to the director below;
not proceeding to T03 (`openubem/geometry/european_nocore.py`, untouched throughout both passes)
without a separate dispatch.

#### T02c — Why the two cut repairs are inert (diagnosis) — completed 2026-09-07

**Artifacts:** instrumentation only, inert by default (`_T02C_ACTIVE = False`,
`scripts/eu21/07_nocore_tests.py:320`; `_t02c_note` `:325-335`; call sites in `donate_leftovers`
`:446,455,457,460,465` and `_clears_donation_gates` `:399,402,405,408,412,415,418`), never enabled
by `main()`/`run_bench()`, left inert per §6's own "reverted or left inert" clause — no behaviour
change when `_T02C_ACTIVE` is `False`. Diagnostic harness (scratch, not committed to the repo):
re-cuts the 344 T01-affected plates with `_bench_recut` against the current (post-T02a/T02b)
`build_flats`/`run_checks`, confirms **69/344 still `C12 FAIL`** (matches CP-2's number exactly),
then, for each of the 69, classifies the DEEPEST stage its whole candidate search (every
`_finish_candidate` call inside `build_flats`, i.e. every candidate tried for that plate, not only
the eventual winner) reaches inside `donate_leftovers`/`_clears_donation_gates`.

**Test status — the four counts, sum to 69:**
- **(a) never reaches `donate_leftovers` with any leftover piece, across every candidate tried: 2**
- **(b) reaches it, but no piece ever exceeds the 0.5× mean-flat-area threshold: 27**
- **(c) above threshold, `_bounded_split_piece` attempted but never resolves a valid split
  (degenerate geometry every time): 1**
- **(d) valid split produced, refused by `_clears_donation_gates` every time: 13** — dominant
  refusing check **C10** (8/13 plates hit it at least once; C4 6/13, C5 4/13, C11 4/13 — a plate
  can hit more than one check across different attempts, so these four do not themselves sum to 13)

A fifth outcome the plan's four buckets did not anticipate, also part of the 69: **26 of the 69
reach a valid split that clears every gate (the repair fires) at least once during the plate's
search, yet the plate is still `C12 FAIL` overall** — the donation succeeds but is not enough by
itself to cross `spread >= 0.50` for that plate. `2+27+1+13+26 = 69`.

**Repair 1** (`cut_wingwise`/`lobes_of` wing decomposition): of the same 69, **18 have >= 2 wings**
(structurally eligible for `cut_wingwise`), **51 have < 2 wings** (`lobes_of` never separates them,
so `cut_wingwise` returns `None` regardless of anything else). `18+51 = 69`.

**Notes:** (a)+(b) = 29/69 (42%) is not near zero, so repair 2 is reachable, not universally
unreachable — but the single largest bucket, (26/69, 38%), is the mechanism firing successfully
and still being insufficient, a capacity gap rather than an unreachability gap, for over a third of
the residual. Repair 1 is structurally inapplicable to 51/69 (74%) regardless of repair 2. No fix
attempted, no threshold widened, per this task's own instruction — diagnosis only.

#### T03 — Carry the change into the engine, prove parity — completed 2026-09-07, gate NOT met, plan stops here

**Artifacts:** extracted (D-EU-95, not re-implemented) from `scripts/eu21/07_nocore_tests.py` into
`openubem/geometry/european_nocore.py`: `_plate_score` (`:1140-1170`, 10-tuple with `c10_ok` +
`spread` inserted) and `_fully_ok` (`:1191-1198`, matching unpack) are byte-identical to the bench
functions. `MIN_SPREAD = 0.50` added (`:1744`) and `checks["C12"]` added to `run_checks`
(`:1875-1881`). `_bounded_split_piece` (new, `:416-463`) is byte-identical to the bench version.
`_clears_donation_gates` (new, `:466-491`) and `donate_leftovers` (`:494-556`) are functionally
identical to the bench versions, minus the T02c `_t02c_note` diagnostic calls (diagnostic-only,
not part of the T02a/T02b functional change, so not carried). `cut_wingwise` needed no change —
confirmed byte-identical to the bench copy already (repair 1 pre-existing, `FINDING 242`).

**Test status:** `python scripts/eu21/09_engine_parity.py --jobs 8` — **gate NOT met.** Fleet:
compared 2,529, input_missing 0, mismatches **verdict 0 / count 0 / check 1,101 / geometry 32**
(required 0/0/0/0). Per district (verdict/count/check/geometry, of N compared): ES-MAD-BERRUGUETE
0/0/386/13 of 955; FR-LYO-HAUTCOEURPENTES 0/0/112/2 of 295; GB-LDN-STDUNSTANS 0/0/36/1 of 75;
IT-BOL-GALVANI2 0/0/567/16 of 1,204. First-20-per-district sample
(`openubem/outputs/eu_evidence/EU-21/engine_parity/parity_<district>_2026-09-03.json`) of the
`check`-kind mismatches is dominated by **C5** (the `show` vertex-count string), then C6, with only
0-1 per district touching C10/C11/C4 in the sample — verdict/pass never flips, but the `show`
string and/or the flat geometry of the WINNING candidate differs from the frozen `_r5` baseline.

**Deviation, quoted, not resolved:** `09_engine_parity.py` compares the engine's
`cut_storey_nocore` output against the four frozen `*_nocore_2026-09-03_r5.json` files (sha256
`fe75c96e...`, dated 2026-09-03, pre-dating this plan), never against a freshly re-cut bench run.
T02a's ranking correction (`D-EU-107 f`) inserts `spread` ahead of the continuous `-pinch_total`
tie-break in `_plate_score`; wherever two or more candidates already tie on cov/C5/C6/C4/C11/C10
(all booleans, unchanged), the WINNING candidate itself can now differ from the one `_r5` recorded,
even though its own checks/verdict still pass — hence 0 verdict/count mismatches but 1,101
check-string and 32 geometry mismatches against `_r5`'s frozen flats. Per this task's own
instruction ("Anything else stops the plan and gets reported, never adjusted away") and §2 hard
rule 2 ("Acceptance is `scripts/eu21/09_engine_parity.py` reporting 0 mismatches... the same gate
CP-1 of the carry-in plan used") — the gate as written is not met. No change made to
`09_engine_parity.py`, the `_r5` JSONs, or the engine's scoring to force it through. **Stopping
here; not proceeding to T04 or CP-3 sign-off. Director resolution needed**: whether the `_r5`
baseline must be regenerated under the corrected `_plate_score` before parity can be re-run, or
whether the gate itself needs a different reference — this plan does not decide that.

#### T03b — Re-point the parity gate at a current baseline — completed 2026-09-07

**Artifacts:** four new baselines, `openubem/outputs/eu_evidence/EU-21/district_plans/<DISTRICT>_nocore_2026-09-07_r6.json`,
written by `python scripts/eu21/08_district_viewer.py --district <D> --tag 2026-09-07_r6
--generic-no-census` for all four districts — every other argument byte-identical to the original
`_r5` invocation, quoted from `docs/docs_ACTIVE/europeanLocations/implementation/DONE/PLAN_eu21-colour-repair-2026-09-03.md:343`:
`python scripts/eu21/08_district_viewer.py --district <D> --tag 2026-09-03_r5 --generic-no-census`.
`scripts/eu21/09_engine_parity.py` gained a `--baseline-tag` argument (default `"2026-09-03_r5"`):
`DISTRICT_FILES` became `DISTRICT_NAMES` (`:45-50`) + a `_district_files(baseline_tag)` builder
(`:53-54`), and `_load_all`/`main` (`:130-145`) thread `args.baseline_tag` through. No other change
to the harness, the engine, or the bench scoring.

**Method:** the four `_r5` files were sha256'd before and after the `_r6` regeneration and are
byte-identical: `ES-MAD 549c2f53...`, `FR-LYO 0907d5c0...`, `GB-LDN 35e580d9...`, `IT-BOL
2059aff2...` (unchanged, confirming `_r5` was read-only throughout). All four `_r6` JSONs parsed
as valid JSON with `tag = "2026-09-07_r6"` and the current cutter's `cutter_sha256`
(`1a1ea4b9...`). Two `09_engine_parity.py --jobs 8` runs followed, `--baseline-tag 2026-09-07_r6`
then the default.

**Results — run A (`--baseline-tag 2026-09-07_r6`):** fleet compared 2,529, input_missing 0,
mismatches **0/0/0/0**. Per district (verdict/count/check/geometry of N compared): ES-MAD 0/0/0/0
of 955; FR-LYO 0/0/0/0 of 295; GB-LDN 0/0/0/0 of 75; IT-BOL 0/0/0/0 of 1,204. Gate met exactly.

**Results — run B (default, `2026-09-03_r5`):** fleet compared 2,529, input_missing 0, mismatches
**0/0/1,101/32**. Per district: ES-MAD 0/0/386/13 of 955; FR-LYO 0/0/112/2 of 295; GB-LDN 0/0/36/1
of 75; IT-BOL 0/0/567/16 of 1,204 — reproducing T03's original numbers exactly. Both `D-EU-107 g`
gates met; transitivity holds (engine ≡ `_r6` exactly, engine vs `_r5` unchanged from T03, so `_r6`
vs `_r5` is the same 1,101/32 drift).

**Test status:** both gates as specified, no adjustment made to reach them.

**Deviations:** none. `_r6` HTML viewers under `plans3D/` are the by-product `08_district_viewer.py`
always writes; not published anywhere, per the ruling's item 5.

**Notes:** `CP-3` remains unsigned (director-only, per §7). T04 not started.

---

#### Director note — gate-battery method, 2026-09-07

🔴 **FINDING 264 — the emitted-token gate battery is self-fulfilling and must never be quoted as a gate
result.** The `_final_2026-09-07/` trees do not persist check outcomes, so every gate battery is a
re-derivation. Two re-derivation routes were used: `gates_fr.py` takes the dwelling count `k` from the
**allocator** (`allocate_european_dwellings` over `_mapped_rows` / `_gb_rows`), while
`gates_<D>_offline.py` takes `k` from the **emitted** `schedules/<stem>/` `F<floor>_dwelling_<idx>`
filename tokens. The emitted route only observes plates the engine already divided successfully — a
plate that failed a check was rerouted or left undivided at emission time and therefore contributes no
`dwelling_N` tokens to be counted, so its failure is invisible to the measurement.

Control run on FR, same district, same `cut_storey_nocore`, both routes:

| route | buildings | plates | C1 | C3 | C4 | C5 | C6 | C10 | C11 | C12 |
|---|---|---|---|---|---|---|---|---|---|---|
| allocator (`gates_fr.py`) | 509 | 726 | 0 | 0 | 2 | 8 | 1 | 9 | 10 | 11 |
| emitted tokens (`gates_fr_offline.py`) | 509 | 641 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |

Join key `osm_id` == `building_id`, 0 unjoined, so the gap is not a join artefact: 85 plates are simply
absent from the emitted route, and every one of the 30 seven-check failures disappears with them.

**Correction, same day, after tracing the failures back to `prepared_buildings.csv`.** The two routes are
not right-and-wrong; they measure **two different populations**, and the original wording of this finding
was too strong. All 22 FR buildings behind the 30 seven-check failures carry
`geometry_outcome = FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT` — the engine declined to divide them,
so those plates were never emitted. Of the 7 FR buildings failing `C12`, 5 are in that same fallback set
and only **2** shipped with a dwelling layout. District-wide FR emission outcomes: 459
`DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`, 25 `..._INTERZONE_MISMATCH_REROUTED`, 25
`FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`.

So the correct standing rule is that **every gate number must name its population**:

- **Shipped population** (emitted-token route, `gates_<D>_offline.py`): of the plates actually emitted as
  dwelling divisions, how many violate a check. This is the number that describes the deliverable, and it
  is the one to quote to an external consumer. FR: 641 plates, 0 seven-check failures, 3 `C12`.
- **Full population** (allocator route, `gates_fr.py`): what the cutter would do on every building given an
  imputed `k`, including buildings the emission refused to divide. This is the number that describes the
  rule's coverage, and it is the one to quote when arguing the rule is sound. FR: 726 plates, 30
  seven-check failures, 11 `C12`.

Differencing the two, or quoting either without its population label, is the actual error. Neither number
is retracted; both are recorded per district.

Consequence for `IT-BOL-GALVANI2`: its full-population number remains **unmeasured** — `_it_rows`
(`scripts/run_eu_s2_district_campaign.py:455-495`) needs two live Bologna OpenData GeoJSON fetches for
`observed_dwellings`, neither is cached (`EU-04/D-EU-22/_cache/` holds only `dati-cpa_2011.zip`), and the
live-fetch embargo is still in force. Its **shipped-population** number is measured and stands, so IT is
not blocked for delivery; only the coverage claim is deferred.

**Owner ruling, 2026-09-07 — IT ships on the shipped-population number alone.** The owner declined to lift
the live-fetch embargo for the two Bologna OpenData GeoJSON endpoints and authorised delivery of
`IT-BOL-GALVANI2` with its shipped-population gate result only. IT's full-population number stays
permanently absent from this arc unless the embargo is lifted later; it must be reported as
**not measured**, never as passing, and never as zero.

#### Director note — full-population control for ES and GB, 2026-09-07

Both districts were re-derived through the allocator route so every district now carries both populations
(`FINDING 264`). Artifacts: `gates_ES-MAD-BERRUGUETE_allocator_2026-09-07.json`,
`gates_GB-LDN-STDUNSTANS_allocator_2026-09-07.json`; the shipped-population files were not overwritten.
Every one of the six gate JSONs now carries a `population` field (`shipped` / `full`), a `population_note`,
and a `finding` pointer, so no number can be quoted without its label.

| district | population | buildings | plates | C1 | C3 | C4 | C5 | C6 | C10 | C11 | C12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ES-MAD-BERRUGUETE | shipped | 1175 | 1533 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 36 |
| ES-MAD-BERRUGUETE | full | 1175 | 1757 | 0 | 0 | 9 | 6 | 5 | 46 | 18 | 54 |
| FR-LYO-HAUTCOEURPENTES | shipped | 509 | 641 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| FR-LYO-HAUTCOEURPENTES | full | 509 | 726 | 0 | 0 | 2 | 8 | 1 | 9 | 10 | 11 |
| GB-LDN-STDUNSTANS | shipped | 706 | 738 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| GB-LDN-STDUNSTANS | full | 706 | 761 | 0 | 0 | 0 | 0 | 0 | 4 | 2 | 4 |
| IT-BOL-GALVANI2 | shipped | 1211 | 1754 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 56 |
| IT-BOL-GALVANI2 | full | — | — | not measured (live-fetch embargo, owner ruling above) |||||||||

`buildings_missing_row = 0` and `cutter_errors = 0` on both new artifacts.

Two method points, both load-bearing for anyone re-running these:

- GB's allocator route needed `_gb_terrace_recovery_rows` appended after `_gb_rows`, mirroring
  `prepare(..., recover_terrace_neighbours=True)`, which is the path the final 2026-09-07 GB campaign used
  (`summary.json` records `terrace_recovery.recovered = 255`). Without it the route drops 255 buildings and
  reports `buildings_missing_row = 255`. This is purely geometric — no network.
- GB is the only district where the two populations agree on `C12` (4 and 4). ES diverges most (36 vs 54).
  The divergence is the undivided-building tail, not a rule change, and must not be reported as a regression.

#### 🔴 FINDING 265 — the carried-over population is not all hash-identical, 2026-09-07

`D-EU-109` T03's spec says the simulate list is *"every building whose `idf_sha256` changed, plus the 255
net-new London buildings — this list, and only this list, is what reaches Speed"*. Two lists were written and
they do not agree:

- `EU-21/division_recovery/simulate_list_2026-09-07.csv` — **2,473** rows (ES 945, FR 254, GB 336, IT 938).
- The four per-district files `EU-11/simulate_list_<CC>_2026-09-07.csv` — **899** rows (ES 274, FR 91, GB 299,
  IT 235). These are `changed + net_new` **after** removing the `FINDING 263` non-deterministic population.

The four Speed fleets were staged from the smaller pair, so **899 buildings were re-simulated and 2,702 were
carried over from the `ceiling82_2026-09-05` harvest**. Carrying over is only sound where the final IDF is
byte-identical to the ceiling82 one. Measured, per district (`prepared_buildings.csv` `idf_sha256` joined to
the ceiling82 manifest on `building_id`):

| district | total | simulated | carried, hash identical | carried, **hash differs** |
|---|---|---|---|---|
| ES-MAD-BERRUGUETE | 1175 | 274 | 230 | **671** |
| FR-LYO-HAUTCOEURPENTES | 509 | 91 | 255 | **163** |
| GB-LDN-STDUNSTANS | 706 | 299 | 370 | **37** |
| IT-BOL-GALVANI2 | 1211 | 235 | 273 | **703** |
| **fleet** | **3601** | **899** | **1128** | **1574** |

`FINDING 263`'s exclusion rule is a rule about the **hash proof** — you cannot read change out of a
non-deterministic hash. It was applied to the **simulation population**, which is a different question: the
shipped IDF for those 1,574 buildings is a different file from the one whose EUI is on record, so publishing
the ceiling82 EUI against it would attribute a number to a file that never produced it. Whether the
difference is only vertex reordering is an assumption, and it has not been measured.

**Disposition.** No EUI may be published for a hash-different carried building until it is re-simulated. The
1,574 are staged as four delta fleets in `FINDING 263`-blind order — FR first (163, it is the GSSCanada
deliverable), then GB (37), then ES (671) and IT (703). The 1,128 hash-identical carries stand as they are;
that carry is exact and needs no run.

Also recorded: `EU-11/<D>_final_2026-09-07/` holds the full district population (FR 509, GB 706, ES 1175,
IT 1211) while the remote fleet dirs hold only the simulate-list subset, so a harvest of a `_final_` tree
reports the carried rows as `rc=<NA>`. That is expected, not a staging defect — GB's first harvest showed
407 such rows against 299 successes. The final manifest must be a **merge** of the delta harvest and the
ceiling82 harvest, with the source of every row recorded.

#### Director note — the hash half of `CP-3`, 2026-09-07

Attempted director-side reproduction and it cannot be done from the persisted artifacts. Reconstructing the
control from `prepared_buildings.csv` vs the ceiling82 manifest, excluding only the
`*_INTERZONE_MISMATCH_REROUTED` population that `geometry_outcome` records, gives FR core-changed 235 against
the 88 T03m reported. The gap is the `near_duplicate_vertex_tolerated_box` half of the `FINDING 263`
exclusion, which is **not** a `geometry_outcome` value and is not stored in any `_final_2026-09-07` tree.
Per-building hash state was persisted for two districts only —
`EU-11/es_hash_control_state.csv` and `EU-11/it_hash_control_state.csv` — so FR and GB have no reproducible
record and the executor's counts for them cannot be re-derived by anyone, including me.

The hash half therefore **stays unsigned**, and `FINDING 265` removes the reason to chase it: once the four
delta fleets land, every building whose IDF hash differs from ceiling82 has been simulated on its own shipped
IDF, so no published EUI depends on the hash proof any more. The proof's remaining value is as evidence that
the `D-EU-109` engine change was surgical, which is a claim about the engine, not about the deliverable.

If it is ever signed, the missing artifact is the one to produce first: a per-building
`<CC>_hash_control_state.csv` for FR and GB carrying both exclusion flags by name, written the same way the ES
and IT ones were.




#### Director note — FR C12 population, 2026-09-07

FR's 11 `C12` plate-failures resolve to **7 unique building ids**, of which 4 are in the
`affected_buildings_2026-09-07.csv` census and 3 are outside it
(`BATIMENT0000000240880119_part0`, `BATIMENT0000000240880572_part0`, `BATIMENT0000000240881274_part0`).
This does **not** contradict CP-2's census figure `FR-LYO 17 → 3`: the emission population includes
plates that were never in the parity census, so the two counts are over different populations and must
not be differenced.

#### Director note — the FR before/after diff is not a regression test, 2026-09-07

The FR before/after comparison (before 507 buildings / 722 plates, after 509 / 726, identical failed-id
sets on all eight checks, 0 new / 0 fixed) is **vacuous as a regression test**. Because checks are not
persisted, both sides were re-derived with today's engine; the run therefore proves only that the
footprint and dwelling-count inputs are stable, not that the engine did not regress. The load-bearing
regression evidence remains CP-2's bench measurement — 0 regressions on the seven checks, 275/344 `C12`
recovery. Do not cite the before/after diff as regression coverage.

### T06a — Merged harvester, one manifest per district (executor may write, director runs)

**What:** a new `scripts/cluster/harvest_eu11_merged.py`. No other file may be created. Only one other file
may be edited: `scripts/cluster/harvest_eu11_district.py`, and only to add rows to `TAGGED_DISTRICT_JOBS`.

**Why:** `FINDING 265`. A harvest of one tree is not the district. The published manifest must merge three
sources and name the source of every row; no EUI may be carried for a building whose shipped IDF differs
from the `ceiling82_2026-09-05` one.

**How:**

1. Register these in `TAGGED_DISTRICT_JOBS` of `harvest_eu11_district.py`:

   | district | `final_2026-09-07` | `delta_2026-09-07` |
   |---|---|---|
   | FR-LYO-HAUTCOEURPENTES | 1311158 | 1311699 |
   | GB-LDN-STDUNSTANS | 1311214 | 1311701 |
   | ES-MAD-BERRUGUETE | 1311215 | 1311703 |
   | IT-BOL-GALVANI2 | 1311244 | 1311708 |

2. `harvest_eu11_merged.py --district <D>` imports `harvest_eu11_district` and calls its `harvest_district`
   once with `tag="final_2026-09-07"` and once with `tag="delta_2026-09-07"`. It does not reimplement the
   SQL, rc, or area logic.

3. Row population = every `building_id` in `EU-11/<D>_final_2026-09-07/prepared_buildings.csv`.

4. `eui_source` per building, first match wins:
   - `delta_2026-09-07` — the delta harvest has a row with `eplus_return_code == 0`.
   - `final_2026-09-07` — the final harvest has a row with `eplus_return_code == 0`.
   - `ceiling82_carry` — `prepared_buildings.csv.idf_sha256` equals the `ceiling82_2026-09-05` manifest's
     `idf_sha256` for that `building_id`, and that row has `eplus_return_code == 0`.
   - `pending_resimulation` — otherwise. Every result column stays blank. This is a published row with no EUI,
     not a dropped row.

5. Output `EU-11/<D>_merged_2026-09-07/<slug>_manifest.csv`, columns =
   `harvest_eu11_district.MANIFEST_COLUMNS` + `eui_source` + `idf_sha256_matches_ceiling82`.

6. Output `EU-11/<D>_merged_2026-09-07/summary.json`: counts per `eui_source`; `n_rows`, `n_with_eui`,
   `n_pending`; `pooled_eui_kwh_m2` = `sum(heating_kwh) / sum(floor_area_m2)` over rows with an EUI, beside
   `pooled_eui_population` naming that subset in words; `ceiling82_pooled_eui_kwh_m2` and the delta; and a
   `disclosures` list. FR's list must contain: stem `cee45cbc2718154c` was rebuilt from 29 dwelling zones to
   8 `one_zone_per_floor` zones with the courtyard filled, so its floor area and EUI denominator differ from
   every earlier manifest.

7. `--dry-run` resolves `eui_source` from local artifacts only, fetches nothing, writes nothing, prints the
   four counts.

**How to test:** `--district FR-LYO-HAUTCOEURPENTES --dry-run`. Report the four counts. Do not run without
`--dry-run`; the delta fleets are still in flight and the director runs the real harvest.

**Hard rules:** no `sbatch`, no `scontrol`, no job submission, no writes under any `*_ceiling82_2026-09-05/`
tree, no code comments, no files beyond the two named above.

#### T06a — Merged harvester — completed 2026-09-07

Artifacts: `scripts/cluster/harvest_eu11_merged.py` (new); `scripts/cluster/harvest_eu11_district.py`
(`TAGGED_DISTRICT_JOBS` only — added the 7 missing `(district, tag)` entries from the T06a table; the
pre-existing `("GB-LDN-STDUNSTANS", "final_2026-09-07"): 1311214` entry already matched the table and was
left as-is).

Deviations: none from the written spec. One interpretation was needed where the spec was silent: "every
result column stays blank" for `pending_resimulation` was read as the 9 post-`weather_sha256` MANIFEST_COLUMNS
(`eplus_return_code` … `energyplus_version`) — the identity/provenance columns through `weather_sha256`
(including `idf_sha256`, needed for the ceiling82 match) are always populated from the district's
`prepared_buildings.csv`.

Test status: `--district FR-LYO-HAUTCOEURPENTES --dry-run` ran clean. Counts: `delta_2026-09-07`=0,
`final_2026-09-07`=0, `ceiling82_carry`=255, `pending_resimulation`=254 (sums to the 509-row population).
Both local tag manifests exist on disk already; `final_2026-09-07`'s `eplus_return_code` is all-NaN (509/509),
consistent with "delta fleets still in flight." No network call made, no directory written under
`EU-11/FR-LYO-HAUTCOEURPENTES_merged_2026-09-07/` (verified absent post-run).

Notes: real (non-`--dry-run`) invocation calls `harvest_district` twice per district (final, delta tags) per
spec item 2 — untested here per the plan's instruction that the director runs the real harvest.

#### T06/T07 — Lyon harvested and restated — completed 2026-09-07

Artifacts: `openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES_merged_2026-09-07/`
(`fr_lyo_hautcoeurpentes_manifest.csv`, 509 rows; `summary.json`);
`FR-LYO-HAUTCOEURPENTES_delta_2026-09-07/` staged evidence dir (`prepared_buildings.csv` copied from the
final tree, `fleet.lst` 163 stems pulled from `EU11_FR-LYO-HAUTCOEURPENTES_delta_2026-09-07`);
`scripts/generate_eu_3d_viewers.py:860-878` (`_load_eu11_eui` now prefers `_merged_2026-09-07`, falls back
to `_ceiling82_2026-09-05`); `openubem/outputs/3D/eu_FR-LYO-HAUTCOEURPENTES_viewer.html` + `_data/` and the
`docs_ACTIVE/europeanLocations/outputs_3D/` mirror, regenerated for Lyon only.

Restatement: pooled EUI **65.935928 → 69.595307 kWh/m²**, `+3.659379` (`+5.55 %`), population
**505 of 509 buildings**. `eui_source`: `final_2026-09-07` 91, `delta_2026-09-07` 159, `ceiling82_carry`
255, `pending_resimulation` 4. Per `FINDING 264` both halves of that number name their population; the
pooled figure is the *shipped* route over the 505 buildings that carry a result column.

Deviations: the delta fleets were built and pushed to Speed without a local `_delta_2026-09-07/` evidence
directory, so `harvest_district` failed on the missing `prepared_buildings.csv`. Resolved by copying the
final tree's `prepared_buildings.csv` (which enumerates the whole 509-building district, not just its own
91-stem fleet) after verifying all 163 delta IDFs are byte-identical to the `idf_sha256` recorded there —
163/163 match, 0 missing, 0 differing. The same staging and verification was done for GB (37/37), ES
(671/671) and IT (703/703) ahead of their harvests. `TAGGED_DISTRICT_JOBS[("FR-LYO-HAUTCOEURPENTES",
"final_2026-09-07")]` remains `1311158`, but stem `cee45cbc2718154c` (task 54) actually ran under job
`1311891`; the only consequence is a blank `run_seconds` for that one row, since job id is used solely for
`sacct` elapsed and the `speed_job_id` column.

Test status: viewer carries 505 non-null and 263 null `"eui"` values over 768 features (509 district + 259
context/excluded); 509 − 505 = 4 `pending_resimulation`, 768 − 509 = 259 context — both reconcile. Manifest
re-measured independently: 509 rows, 505 non-blank `eui_kwh_m2`.

Notes: four buildings ship as `pending_resimulation` with every result column blank rather than carrying an
EUI from a different IDF (`FINDING 265`): `dd1d33feca834272` (`FINDING 210` recurrence, fatal),
`5e0376cc50cbea69` (5 h 10 m with a 0-byte `eplusout.err`, no `task.rc`), and delta tasks 147/148
(`aec18ccb210f0bca`, `4a1d49fc78fa56c6`) which were still running when the owner authorised harvesting at
505. `summary.json` carries the `cee45cbc2718154c` rezoning disclosure (29 dwelling zones → 8
`one_zone_per_floor`, courtyard filled) required by T06a. London, Madrid and Bologna EUIs remain stale.

#### T06/T07 — London harvested and restated — completed 2026-09-07

Artifacts: `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_merged_2026-09-07/`
(`gb_ldn_stdunstans_manifest.csv`, 706 rows; `summary.json`), produced by
`scripts/cluster/harvest_eu11_merged.py --district GB-LDN-STDUNSTANS` from the `_final_2026-09-07` harvest
(job `1311214`, 299 tasks) and the `_delta_2026-09-07` harvest (job `1311701`, 37 tasks). Viewer
regenerated by `scripts/generate_eu_3d_viewers.py::build_district('GB-LDN-STDUNSTANS')` and mirrored to
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`.

Restatement: **120.064327 kWh/m² over 706 of 706 buildings**, replacing the ceiling82 **97.081151** — a
**+22.983176 kWh/m²** move, and the population also changed (ceiling82 pooled 451 buildings, the restated
number pools all 706). `eui_source` counts: `final_2026-09-07` 299, `delta_2026-09-07` 37,
`ceiling82_carry` 370, `pending_resimulation` 0. Per `FINDING 264` the pooled figure is the *shipped*
route over the full 706-building allocator population; unlike Lyon there is no pending subset, so the
shipped and full populations coincide here. No `FINDING 264` disclosure and no rezoning disclosure ride
with this number — `disclosures` is empty.

Deviations: none. The `_delta_2026-09-07` evidence directory had already been staged and hash-verified
ahead of the harvest (37/37 delta IDFs byte-identical to `idf_sha256` in the final tree's
`prepared_buildings.csv`, 0 missing, 0 differing), so the `prepared_buildings.csv` failure seen on Lyon did
not recur.

Test status: delta fleet drained with 37 `out/` directories, 37 `task.rc` = 0, 37 `eplusout.sql`, 0 fatal;
main fleet 299/299 `COMPLETED`. Viewer carries 706 non-null and 645 null `"eui"` values over 1,351 features
(706 district + 645 context/excluded); 706 − 706 = 0 `pending_resimulation`, 1351 − 706 = 645 context —
both reconcile, and both mirror copies measure identically.

Notes: the district's `_final_` fleet reports `success=299 failed=407` in isolation, which is the
`FINDING 265` artefact, not a failure — the 407 "failed" rows are buildings that fleet never simulated and
that the merge resolves as `ceiling82_carry` (370) or `delta_2026-09-07` (37). The `_final_`-only pooled
figure of 149.9371 kWh/m² and the `_delta_`-only 69.2127 kWh/m² are per-fleet diagnostics and may not be
quoted as district EUIs. Madrid and Bologna remain stale.

#### T06/T07 — Madrid harvested and restated — completed 2026-09-08

Artifacts: `openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE_merged_2026-09-07/` (summary.json +
`es_mad_berruguete_manifest.csv`, 1,175 rows), regenerated viewer
`openubem/outputs/3D/eu_ES-MAD-BERRUGUETE_viewer.html` + `_data/` mirrored to
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`.

Restatement: **80.694006 kWh/m² over 1,166 of 1,175 buildings**, replacing the ceiling82 **77.153998** — a
**+3.540008 kWh/m²** move, and the population also changed (ceiling82 pooled 1,174 buildings and reported
10 failed; the restated number pools 1,166 and holds 9 back as `pending_resimulation`). `eui_source`
counts: `final_2026-09-07` 272, `delta_2026-09-07` 664, `ceiling82_carry` 230, `pending_resimulation` 9.
`disclosures` is empty. The 9 pending rows carry blank result columns, not an EUI from a different IDF
(`FINDING 265`).

Deviations: none. Both `_final_` and `_delta_` IDF trees were staged locally ahead of the harvest
(1,181 and 671 IDFs), so neither the `prepared_buildings.csv` failure seen on Lyon nor a plan-vintage
mismatch recurred.

Test status: main fleet 1311215 drained 272 rc=0 / 2 rc=1; delta fleet 1311703 drained 671 `out/`
directories, 664 rc=0 / 7 rc=1. Five-line audit all pass — summary population string matches the counts;
manifest 1,175 rows / 1,166 non-null EUI, all 9 pending rows blank; viewer 1,398 features with 1,166
non-null and 232 null `"eui"` (1,398 − 1,175 = 223 context/excluded plus the 9 pending, which reconciles);
EU-21 checks joined 1,181 hit / 0 miss; both mirror copies md5-identical to the source.

Notes: the `_final_`-only pooled figure of 112.3050 kWh/m² and the `_delta_`-only 74.4311 kWh/m² are
per-fleet diagnostics — the same `FINDING 265` artefact as London (`success=272 failed=903` in isolation)
— and may not be quoted as district EUIs. Layout states across the viewer population: 1,038 `ruled`,
143 `massing_box`, 13 `no_idf`, 204 unclassified. Bologna remains stale.
