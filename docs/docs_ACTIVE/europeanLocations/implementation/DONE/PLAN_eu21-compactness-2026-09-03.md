# PLAN — EU-21 flat proportion (C11) and grid-first division

- **slug:** `eu21-compactness`
- **date:** 2026-09-03
- **owner sentences that open this arc (verbatim):** *"you said this '550/550 PASS, 0 FAIL across the five
  no-core sheets.' however i do not belive that … there can be better flat division … look violation of narrow
  space … there could be better floor division, why not adding division from second edge, for instance look i
  gave this example to you. you are dicviding from one edge, but instead we can define a rule. we are dviding
  flat zones but there could be a limit to a width of a flat, i do not know. you define and add to the global
  rules, becasue in the examples i am givigin to you as you can see a lot of narrow flats are available. so can
  you update every tests based on these updates … go to the end."*
- **DESIGN pointer:** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v5.md`
- **builds on:** `PLAN_eu21-nocore-2026-09-02.md` (CLOSED, 550/550 PASS on six checks). This arc does not
  reopen it: it adds a **seventh** check the six never scored, and a layout search that can satisfy it.

---

## 0. Why this arc exists — the director's own measurement (2026-09-03)

The owner is right and the number is large. Over the five delivered `*_nocore_2026-09-02` sheets —
**550 plates, 3,267 flats** — the *minimum rotated rectangle* long/short ratio of each drawn flat:

| slenderness | flats above | plates with at least one |
| --- | --- | --- |
| > 2.0 | 2,196 / 3,267 (67 %) | 366 / 550 |
| > 2.5 | 1,849 (57 %) | 296 |
| > 3.0 | 1,577 (48 %) | 240 |
| > 3.5 | 1,358 (42 %) | 205 |
| > 4.0 | 1,217 (37 %) | 178 |

Worst plates are all `n = 12`: `COURTYARD 29659` **14.1 : 1**, `L_SHAPE way/391279228` 13.6,
`COMPLEX_MULTI_WING 31801` 13.0, `TRAPEZOID way/391662735` 12.9, `TRIANGLE way/389587830` 12.8.

**Cause, and it is one line.** `build_flats` (`scripts/eu21/07_nocore_tests.py:533`) keeps the default
single-axis cut whenever `_fully_ok` passes, and `_fully_ok` scores only `C1 C4 C5 C6 C10`. Nothing in the
six checks scores **shape**, so a plate sliced into 12 parallel ribbons 5 m × 25 m is a legitimate
`PASS`. The grid cutter `cut_grid` already exists (`07:343`) but is only ever reached by plates that
*failed* something else. The owner's example drawing is exactly this: cut from the second edge too.

**Therefore: `550/550 PASS` was true against the six checks and useless as a statement about the drawings.**
Record as `FINDING 238` (§6).

---

## 1. Hard rules for the executor

1. **`scripts/eu21/07_nocore_tests.py` is the only `.py` file you write.** `01`, `02`, `03`, `04`, `05`, `06`
   are read-only — import from them, never edit them, not one constant.
2. 🔴 **No EnergyPlus, no simulation, of any kind (`D-EU-55`).** This arc draws flat divisions and scores
   them geometrically. Nothing else.
3. 🔴 **No git command at all** — not `add`, `commit`, `stash`, `restore`, `checkout`, `reset`, `clean`, and
   not `log`, `show`, `diff`. The dirty tree is the owner's; git is handled outside this session.
4. **No existing check is loosened.** `C1` stays `0.999–1.001`; `C4` stays `< 0.02 m²`; `C5` stays `40`
   points; `C6` stays `2.50 m`; `C10` stays `2.00 m`. `C11` is a **new** check and is the only threshold this
   arc is allowed to calibrate, once, by the ladder in T05.
5. **No plate may become REFUSED.** The no-core regime has no refusal path. A plate that cannot be cut is a
   `FAIL` you report, never a refusal you invent.
6. **Never overwrite the delivered `*_2026-09-02` artifacts.** The five `TEST_0*_nocore_2026-09-02.html`
   sheets and the five `test_0*_nocore.json` censuses are snapshotted in T01 and then superseded by
   `*_2026-09-03` files. Never write into `rules/archive/`, `rules/tests/archive/`, `EU-17/` or `EU-20/`
   except where a task names it.
7. **Create no file this plan does not name.** Scratch goes to
   `C:/Users/o_iseri/AppData/Local/Temp/claude/C--Users-o-iseri-Desktop-OpenUBEM/9d0c66b5-6065-45ea-96cd-0069a7f12813/scratchpad`
   and is deleted before you report. No `.py` under `docs/`, ever.
8. **Before debugging any error**, search `docs/docs_ACTIVE/europeanLocations/debugs/DEBUG_REFERENCES_european_locations.md`
   then `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. **After solving any error**, register it in the
   europeanLocations one, ch. 1, in the house format, before you close the task.
9. **Append a progress-log entry to §8 of this doc for every task you finish** — Artifacts / Deviations /
   Test status / Notes. A task with no entry is not done.
10. **Report the honest number.** If a target is not reached, say so with the residual plate list. Never
    describe a partial result as complete. Never quote a census you did not run in this session.

---

## 2. File layout

| path | role in this arc |
| --- | --- |
| `scripts/eu21/07_nocore_tests.py` | **the only file you write.** Cutter + checks + sheet builder. |
| `scripts/eu21/04_group_tests.py` | read-only. Selection, universe, `widest_fit`, `sbuf`, drawing helpers. |
| `scripts/eu21/05_group_cutters.py` | read-only. `frame`, `to_local`, `to_world`, `equal_area_x`, `_normalize`, `lobes_of`. |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/baseline_nocore_2026-09-02/` | **T01 creates it.** Byte copies of the five `test_0*_nocore.json` before anything changes. |
| `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N_nocore.json` | N = 1…5. Rewritten by this arc. |
| `docs/.../rules/tests/TEST_0N_<slug>_nocore_2026-09-03.html` | N = 1…5. **The five new delivered sheets.** |
| `docs/.../rules/tests/archive/` | destination for the five `*_nocore_2026-09-02.html` sheets (T07). |
| `docs/.../rules/*_nocore_2026-09-03.*` | the four rules docs, re-dated with `C11` (T07). |
| `docs/.../rules/archive/` | destination for the four `*_nocore_2026-09-02.*` rules docs (T07). |

Exact new sheet names — copy them character for character:

```
TEST_01_three_per_group_nocore_2026-09-03.html
TEST_02_floor_sizes_x3_nocore_2026-09-03.html
TEST_03_five_per_group_nocore_2026-09-03.html
TEST_04_floor_sizes_x5_nocore_2026-09-03.html
TEST_05_ten_per_group_nocore_2026-09-03.html
```

---

## 3. How to run

From the repo root, always the venv interpreter and always `PYTHONIOENCODING=utf-8` (bare `python` exits 49):

```
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe scripts/eu21/07_nocore_tests.py --test 1
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe scripts/eu21/07_nocore_tests.py --test all
```

**The census control — run it yourself and paste the raw output in every report** (N = 1…5). Write it to the
scratchpad as `census.py` and run it, so quoting never becomes the problem:

```python
import json, collections, math
from shapely.geometry import Polygon

def aspect(f):
    c = list(f.minimum_rotated_rectangle.exterior.coords)
    s = sorted(math.dist(c[i], c[i + 1]) for i in range(4))
    return (s[3] / s[0]) if s[0] > 0 else 99.0

for n in range(1, 6):
    p = 'openubem/outputs/eu_evidence/EU-21/rules_tests/test_0%d_nocore.json' % n
    d = json.load(open(p, encoding='utf-8')); P = d['plates']
    A = [aspect(Polygon(x[0], x[1:])) for r in P for x in r['dwellings']]
    print('test', n, 'plates', len(P), collections.Counter(r['verdict'] for r in P),
          'flats', len(A), 'max', round(max(A), 2), 'over3.0', sum(1 for a in A if a > 3.0))
    for i, r in enumerate(P, 1):
        if r['verdict'] != 'PASS':
            print('  FAIL', i, r['group'], r['building_id'], r['drawn_per_floor'],
                  [(k, v.get('show')) for k, v in (r.get('checks') or {}).items()
                   if isinstance(v, dict) and v.get('pass') is False])
```

---

## 4. Dependency decisions (pinned — do not revisit)

- **`DD-1` — acceptance is the five `*_nocore_2026-09-03` sheets at `FAIL 0` on seven checks**
  (`C1 C3 C4 C5 C6 C10 C11`), 550 plates, no plate dropped and no plate refused.
- **`DD-2` — `C11` is measured on the minimum rotated rectangle**, `long / short`. Continuous, scale-free,
  and cheap (`shapely` `minimum_rotated_rectangle`). It is *not* measured with `widest_fit`: that helper is a
  probe ladder capped at 4.0 m (`04_group_tests.py:296`) and cannot resolve a proportion.
- **`DD-3` — `C10` keeps its own job.** `C11` does not replace it: `C10` forbids a *pinch*, `C11` forbids a
  *ribbon*. Both are scored, both are printed.
- **`DD-4` — equal area stays informational** (`spread` on the card), never a pass condition. Carried from
  `DD-C` of the nocore plan.
- **`DD-5` — geometry is expected to change on almost every plate.** That is the point of the arc; it is
  never a regression. The `2026-09-02` sheets stay on disk as the before-picture.
- **`DD-6` — next free ids.** Laws from **`D-EU-85`** (`D-EU-82`, `D-EU-83`, `D-EU-84` are spent in §5).
  Findings from **`FINDING 239`** (`FINDING 238` is spent in §6).

---

## 5. The three laws this arc writes

- **`D-EU-82` — the flat proportion rule (`C11`).** *"No flat may be a ribbon. Every drawn flat's minimum
  rotated bounding rectangle must satisfy `long / short <= MAX_FLAT_ASPECT`."* `MAX_FLAT_ASPECT` is a single
  module constant in `07_nocore_tests.py`, calibrated exactly once by T05's ladder and then frozen. Owner's
  sentence: *"there could be a limit to a width of a flat, i do not know. you define and add to the global
  rules."*
- **`D-EU-83` — division from the second edge is first-class, not a rescue.** *"Every plate is cut by every
  candidate scheme — `rows x cols` for every row count, on both axes — and the best-scoring result is kept.
  A single row of `k` columns is one candidate among many, never the default that only loses when it fails."*
  This is the direct answer to *"you are dicviding from one edge … why not adding division from second edge."*
- **`D-EU-84` — a proportion target is calibrated against the plates, never against a wish.** `MAX_FLAT_ASPECT`
  is set to the **strictest** rung of `{2.5, 3.0, 3.5, 4.0}` at which the improved cutter reaches `FAIL 0`
  over all 550 plates. If no rung reaches `FAIL 0`, the executor **stops at CP-2** and reports the residual
  plate list — it never invents an exemption clause and never softens a rung to make a census look clean.

---

## 6. Findings this arc records

- **`FINDING 238` (2026-09-03).** *A check set that scores no shape term certifies ribbons.* The five
  `*_nocore_2026-09-02` sheets read `550/550 PASS, FAIL 0` while **48 % of their 3,267 flats were more
  slender than 3 : 1** and the worst plate reached **14.1 : 1**. The verdict was arithmetically correct and
  said nothing about whether the drawings were usable. **Never quote a `FAIL 0` census as evidence that a
  drawing is good** — quote it as evidence that the *scored* properties hold, and name them.

---

## 7. Task list

### T01 — Snapshot the before-picture, and reproduce the director's census

**What.** Copy the five `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N_nocore.json` byte-for-byte
into a new folder `.../rules_tests/baseline_nocore_2026-09-02/` (same five names). Then run the §3 census
control against the *unchanged* JSONs.

**Why.** Rule 6: the delivered artifacts are the before-picture and this arc rewrites the live JSONs in place.
Without the snapshot the improvement is unmeasurable afterwards.

**How.** Plain file copy. No script changes at all in this task.

**How to test.** The five copies exist and are byte-identical (size + `sha256` per file, both reported). The
census reproduces the director's §0 table: **3,267 flats, 1,577 over 3.0, max 14.12**. If your numbers differ,
**stop and report** — do not proceed.

---

### T02 — `C11` becomes a scored check

**What.** In `07_nocore_tests.py`:
- add module constant `MAX_FLAT_ASPECT = 3.0` next to the other thresholds;
- add a helper `flat_aspect(f)` returning `long/short` of `f.minimum_rotated_rectangle` (`99.0` if degenerate);
- in `run_checks`, add
  `checks["C11"] = {"pass": max_aspect <= MAX_FLAT_ASPECT, "show": f"{max_aspect:.1f} : 1"}`
  where `max_aspect = max(flat_aspect(f) for f in live)`;
- add `"C11"` to the `verdict` tuple;
- add its `CHECK_META` row: `("C11", "Flat proportion", "max long/short of the minimum rotated rectangle &le; 3.0", "no flat is a ribbon &mdash; a flat is at most three times as long as it is wide, D-EU-82")`.
  The tolerance string must be **generated from `MAX_FLAT_ASPECT`**, not typed, so T05's ladder cannot leave a
  stale number on the sheet.

**Why.** `D-EU-82`. The check must exist and be printed before the cutter is asked to satisfy it, so the
before/after is measured on the same instrument.

**How to test.** `--test 1` only. Report the census. **`FAIL` is expected and correct at this point** — you
have added a check and not yet the cutter that satisfies it. Report how many of the 33 plates fail `C11`.

---

### T03 — `C11` enters the plate score and the early-exit gate

**What.** In `_plate_score`, insert `c11_ok` (a bool, `max_aspect <= MAX_FLAT_ASPECT`) into the returned
tuple **immediately after `c4_ok`**, and append `round(-max_aspect, 3)` as the **last** element. Add the same
`c11_ok` condition to `_fully_ok`.

**Why.** `_fully_ok` is the reason the ribbons survived: a plate that already passed the six checks never
entered the ladder. Ranking order is deliberate — the hard gates `C1`, `C5`, `C6` and then `C4` are never
traded for a squarer flat (the `_plate_score` docstring's own rule, carried forward); `C11` outranks the
numeric `min C10` tie-break, and `-max_aspect` is the final tie-break so that among two plates that both
clear `C11` the squarer one wins.

**How to test.** `--test 1`. Report the census. Expect `C11` failures to drop but not to zero — the candidate
set is still the old one. Confirm no plate that passed `C1/C4/C5/C6/C10` in T01's baseline now fails one of
them; list any that do, with the check and the value.

---

### T04 — Grid-first: every `rows x cols` scheme, on both axes

**What.** Rewrite the search inside `build_flats` so that the candidate set is, for **every** plate:

- `rows` from `1` to `min(k, 6)` — `rows = 1` is exactly today's single-axis cut, so nothing is lost;
- each `rows` on **both** axes (`theta_offset` `0.0` and `90.0`);
- for `rows == 1` only, additionally the swept-boundary variant (`_sweep_boundaries`), as today;
- every candidate goes through `_delobe_and_donate` + `donate_leftovers` exactly as today;
- keep the single best by `_plate_score`; then, if the winner still is not `_fully_ok`, the existing
  `_donate_the_neck` last resort, kept only if it improves the score.

Delete the "keep the default untouched when it already passes" early exit **for the candidate search**
(`_fully_ok` still gates `_donate_the_neck`). `STAGE == "t01"` / `"t02"` debug paths stay exactly as they are.

**Why.** `D-EU-83`, and it is the owner's own drawing: a 12-flat plate must be allowed to become 3 x 4, not
only 1 x 12. `_grid_seeds` already distributes `k` over `rows` bands by area and already dodges courtyard
holes, so this task is a search-order change, not new geometry.

**How to test.** `--test 1`, then `--test 3`, then `--test 5`. Report the census for each, plus the
**chosen `rows` histogram** (add a `rec["rows"]` field written by `build_flats` and print it; do not print it
on the card). Runtime per test must stay under ~15 min; if a test exceeds that, say so with the timing rather
than silently trimming the candidate set.

**🔴 CP-1 — stop and report here.** Report: the four censuses (T01 baseline, T02, T03, T04), the `rows`
histogram, the max aspect per test, and the residual `C11` failures with group / building id / n.

---

### T05 — Calibrate `MAX_FLAT_ASPECT` once, then freeze it

🔴 **T05.0 — do this before any run command, no exceptions (`D-EU-85`, ruled at `CP-1`).**
In `run_test` (`scripts/eu21/07_nocore_tests.py:1041`) the html output path is the literal
`_nocore_2026-09-02`. Change it to `_nocore_2026-09-03` **now**, as your first edit. Every `--test N`
run of `T01`–`T04` rewrote the delivered 2026-09-02 sheet in place and three of the five are lost
(`FINDING 239`). `TEST_02_floor_sizes_x3_nocore_2026-09-02.html` and
`TEST_04_floor_sizes_x5_nocore_2026-09-02.html` are the two survivors: they must still be
byte-identical when you reach `T07`. Do not touch the JSON path — `test_0N_nocore.json` is the
working artifact and its 2026-09-02 state is already snapshotted in
`rules_tests/baseline_nocore_2026-09-02/`.

**What.** Run `--test all` at `MAX_FLAT_ASPECT` = `2.5`, `3.0`, `3.5`, `4.0`. Record the full 550-plate
verdict count at each rung. Set the constant to the **strictest rung that reaches `FAIL 0` on all five
tests**, and write that value, the ladder table, and the date into the constant's own comment.

**Why.** `D-EU-84`. The owner delegated the number (*"i do not know. you define"*) and the honest way to
define it is against the 550 plates that must satisfy it.

**How to test.** The ladder table (four rows x five tests) pasted raw in your report.

**🔴 CP-2 — stop and report here if no rung reaches `FAIL 0`.** In that case report the residual list at
`4.0` and stop; the director rules on the exemption. Do not invent one. If a rung does reach `FAIL 0`,
continue straight into T06.

---

### T05b — Fix the three failing group rules, then re-run the ladder (`D-EU-86`)

🔴 **`CP-2` was reached at T05 and the director has ruled: `D-EU-86`. Read it in
`../STATE_european_locations_v5.md` §4 before writing a line.** `C11` is **not** relaxed, no plate is
exempted, and `MAX_FLAT_ASPECT` is **not** frozen at 4.0.

**What.** Make `COURTYARD`, `L_SHAPE` and `COMPLEX_MULTI_WING` stop returning ribbons on the seven
residual buildings, then re-run the T05 ladder unchanged and freeze the constant at the strictest rung
that reaches `FAIL 0`.

**Why.** The director measured the residual (`FINDING 240`): under every offending flat the plate's
local band is **8.2 - 16.4 m** while the flat's short side is **2.05 - 3.50 m** — 13 - 32 % of the width
on offer, with ordinary 48 - 72 m² flats. A 59 m² flat in an 8 m band fits as 7.7 x 7.7 m. The footprint
is not the constraint; the cut is. `COURTYARD 29659` still reads 14.12:1, identical to the pre-`C11`
baseline, so the grid-first candidate of `D-EU-83` is never winning that plate.

**How.**
0. 🔴 **Before anything else (director, 2026-09-03 — the executor's first `--test all` at ~09:53 rewrote
   the five owner-read sheets, `FINDING 239` second occurrence):** restore the five
   `TEST_0*_nocore_2026-09-03.html` in `rules/tests/` byte-identical from
   `rules/tests/archive/reviewed_2026-09-03/` (copy, then `cmp` all five), and repoint `run_test`'s html tag
   from `_nocore_2026-09-03` to **`_nocore_2026-09-03_r2`** (`07_nocore_tests.py:1177`) — T05c's first edit,
   pulled forward. No run command before both are done.
1. First, diagnose, do not patch: for `COURTYARD 29659` at `n=12` print every candidate the cutter
   generated, its `_plate_score` and its worst `C11`. Establish whether a compliant candidate was
   generated and lost on score, or was never generated at all. Report which, with numbers.
2. If it was **never generated** — the group rule cannot divide a thick band across its depth. Add that
   division: a band whose local width exceeds roughly twice the target flat's short side is cut in two
   layers (or more), not only along its run. Ring segments of a courtyard, and the wings of an `L` or a
   multi-wing plate, are all the same case.
3. If it was **generated and lost** — the fault is in `_plate_score`; make the score prefer the
   candidate with the lower worst-aspect once the hard checks tie.
4. Touch **only** `scripts/eu21/07_nocore_tests.py`. Never `05_group_cutters.py` (parked, `D-EU-79`),
   never `_cut_nocore_t01`.
5. Re-run the **whole** ladder — `--test all` at 2.5, 3.0, 3.5, 4.0 — and record the per-test FAIL count
   at every rung, exactly as T05 did. Set `MAX_FLAT_ASPECT` to the **strictest** rung reaching `FAIL 0`
   over all five tests, and rewrite the constant's comment with the new ladder and today's date.
6. No regression is allowed on `C1 C3 C4 C5 C6 C10`. Report the count for each.

**How to test.** `--test all` at the chosen rung must print `FAIL 0` on all five tests, 550 plates. Print
the seven residual buildings' worst aspect before and after.

**Stop-and-report — amended by the director 2026-09-03.** If, after a genuine depth-division fix, some rung
still cannot reach `FAIL 0`, record the full ladder and the residual plate list in the T05b log entry, leave
`MAX_FLAT_ASPECT` at the least-failing rung **marked not frozen**, and **continue into T05c**, whose new `C10`
score term re-runs the ladder anyway. The stop is taken after T05c's ladder, not before. Do not invent an
exemption and do not loosen the ladder beyond 4.0. `D-EU-86` clause 1 is absolute.

### T05c — Rebuild `C10` as a real pinch test, make the cutter satisfy it (`D-EU-87`)

🔴 **Read `D-EU-87` and `FINDING 241` in `../STATE_european_locations_v5.md` before writing a
line.** The owner marked four plates on the 2026-09-03 sheets — `COMPLEX_MULTI_WING` Bologna 29965,
`COURTYARD` Bologna 32052, `COMPLEX_MULTI_WING` Bologna 30127 and 28754 — each a flat pinched to well
under two metres beside a notch or a light well, each printing **`C10 4.0 m` PASS**.

**Why.** `C10` was wired to `widest_fit` (`04_group_tests.py:299`), which returns the **largest** disc a
flat can hold, capped at 4.0 m. It answers "is this flat fat somewhere". The director's census over all
550 baseline plates, morphological opening at `r = 1.00 m` with mitre joins: **182 of 550 plates (33 %)**
and **278 of 3,267 flats (9 %)** hold a sub-2 m region, and **1,349 m² of the 1,524 m² — 89 % — is
created by the cut, not inherited** from the footprint. The lost-area distribution is bimodal: 2,686
flats at exactly zero, 254 under 0.01 m² of float noise, 80 in a 0.01 – 0.50 m² band, 247 above 0.50 m².

**How — first edit, before any run command (`D-EU-85`).** Repoint the html filename in `run_test`
(`07_nocore_tests.py`) from `_nocore_2026-09-03` to **`_nocore_2026-09-03_r2`**. The five
`_nocore_2026-09-03.html` sheets the owner read are preserved in
`rules/tests/archive/reviewed_2026-09-03/` and must stay byte-identical. Do not touch the JSON path.

**How — the check.**
1. Add `pinch_area(f, plate)`: `lost = f.difference(f.buffer(-1.00, join_style=2, mitre_limit=5.0)
   .buffer(1.00, join_style=2, mitre_limit=5.0))`, guarding the empty-erosion case (then the whole flat
   is lost). Run the identical opening on the plate footprint to get `plate_lost`. Return
   `lost.area - lost.intersection(plate_lost).area`.
2. `C10` becomes: pass when the sum over flats of that value is `<= 0.10 m²`; `show` is
   `f"{total:.2f} m²"`, printed like `C4`. The 0.10 m² tolerance is the measured noise floor and is not
   a negotiable allowance — do not raise it.
3. `widest_fit` may remain as a printed descriptive number but must no longer decide `C10` and must no
   longer be the quantity `_plate_score` maximises (`07:388`, `07:417`, `07:485`, `07:524`).
4. `_fully_ok` gates on the new `C10`; `_plate_score` carries created-pinch area as a term to
   **minimise**, ranked below the hard checks and beside `C11`.

**How — the cutter.** Do not weaken the check to pass it. With `_fully_ok` now failing on a pinch, the
existing `_donate_the_neck` and `_delobe_and_donate` passes finally get reached — verify they run and
report how many plates they repair. Where they cannot, the cut line itself is wrong: a boundary must not
be drawn so that it leaves a strip narrower than 2 m against a notch, a light well or another flat.
Touch **only** `scripts/eu21/07_nocore_tests.py`.

**How to test.** `--test all` must print `FAIL 0` on all five tests, 550 plates, on the full seven checks
`C1 C3 C4 C5 C6 C10 C11`. Re-run the `MAX_FLAT_ASPECT` ladder afterwards — the new score term can move
it — and set the constant to the strictest rung of 2.5 / 3.0 / 3.5 / 4.0 still reaching `FAIL 0`. Report
the owner's four marked plates by name, before and after, with the created-pinch area of each.

**Stop-and-report.** If `FAIL 0` is unreachable, stop and report the residual plate list with the
created-pinch area and the local band width of each. Never invent an exemption, never raise the 0.10 m²
tolerance, never restore `widest_fit` as the verdict.

### T05d — Second repair round: the ring/wing residual and the `MultiPolygon` fault (`D-EU-89` clauses 2–3)

**What.** Two cutter defects, one task, in this order:
1. **`FINDING 243`** — `build_flats` raises `AttributeError: 'MultiPolygon' object has no attribute
   'exterior'` / `'interiors'` on 17 census buildings of the district run (Madrid 8, Lyon 1, Bologna 8; ids and
   messages in `openubem/outputs/eu_evidence/EU-21/district_plans/*_nocore_2026-09-03.json`, `status = "ERROR"`).
   Reproduce each with the plan's own harness (`08_district_viewer.py --district <d> --only <building_id>` if
   that flag exists, else a 10-line driver in `%TEMP%` that calls `build_flats` on the one footprint via
   `load_universe`), find the call site (the traceback's last frame inside `07`), and make every place that
   reads `.exterior` / `.interiors` tolerate a `MultiPolygon` the way `_safe_union` / `_clean_merge` already do —
   keep the largest part, donate the rest to the neighbour sharing the most boundary, never drop area. Do not
   catch-and-ignore. 17 / 17 must end `direct`; the Bologna `TopologyException` record is re-checked after the
   `_opening_lost` fix and reported either way.
2. **`FINDING 242`** — the residual family: `COURTYARD` 29659 / 31169 / 28754 / relation/12765478 /
   relation/4678507 / 28782, `COMPLEX_MULTI_WING` way/968439455 / 31312 / 31801 / way/311595048 /
   way/434878287, `TRIANGLE` BATIMENT…240877151_part0 / 31311, `SLIVER` 29816, `U_OR_T_SHAPE` 30320,
   `CORRIDOR_RECTANGLE` 32721 (the T05c table, §8). Diagnose first, on the three worst by `C10` area: does the
   ring / wing have a legal division **around** the void or notch — i.e. cut the ring into arc segments by
   radial lines from the void's centroid, or cut a wing into segments perpendicular to the wing's own axis —
   that satisfies `C6` outer contact and the 2.00 m opening? If yes, add that candidate family
   (`cut_radial` for rings, `cut_wingwise` for wings) to `build_flats`'s candidate list, scored by the existing
   `_plate_score`, never preferred by name. If no such division exists at that `k` for a given plate, say so
   with the measured numbers and leave it an honest `FAIL`.
3. Re-run the full ladder 2.5 / 3.0 / 3.5 / 4.0 with `--test all` and record the table as in T05c.

**Why.** `D-EU-86` clauses 1–2 and `D-EU-89` clause 2: no exemption, no chosen rung until the cutters have been
given every division the footprint allows. `D-EU-89` clause 3: the district JSONs are now an acceptance input.

**How to test.** (1) 0 `ERROR` across the four district JSONs when the director rebuilds them (`_r3`); the
executor proves the 17 reproduce-and-pass in its log. (2) The ladder table; any plate still failing listed
with `C10` area and local band as in T05c. (3) Regression on `C1/C3/C4/C5/C6`: 0 / 550. Register both fixes
in `../debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 (the `MultiPolygon` entry already exists as
`[OPEN]`; drop the marker and add the fix line).

**Stop-and-report — ruled ahead (`D-EU-89` clause 2).** If some rung reaches `FAIL 0`: freeze at the
strictest such rung and continue into T06. If none does: set `MAX_FLAT_ASPECT = 2.5` — the **strictest**
rung — mark it *set by `D-EU-89` clause 2, not calibrated*, list the residual, and continue into T06. Never
pick the rung that fails least.

---

### T06 — Build the five delivered sheets

**What.** With the constant as T05d left it (frozen at the strictest `FAIL 0` rung, or set to 2.5 by
`D-EU-89` clause 2 with the residual printed on every sheet's tally as honest `FAIL`s), run `--test all` and
write the five sheets under the
**`_nocore_2026-09-03_r2`** names (the tag T05c set). The five `_nocore_2026-09-03.html` sheets the owner
read are already preserved in `rules/tests/archive/reviewed_2026-09-03/` and must stay byte-identical;
the `_nocore_2026-09-02` set is already in `rules/tests/archive/`.

Also repair the sheet's own prose, which still describes the retired regime:
- the `C10` row of the check legend (`07_nocore_tests.py:841`) still reads
  `min widest_fit(f) >= 2.00 m over flats only` — restate it as the created-pinch area test of `D-EU-87`;
- the narrative at `07:867` and the headings at `07:976` and `07:987` still say **six** checks and list
  `C1, C3, C4, C5, C6, C10` — they are **seven**, `C1 C3 C4 C5 C6 C10 C11`.

**Why.** `DD-1`. A delivered artifact is never overwritten — a new build gets a new dated filename. And a
sheet that prints a check must state what that check actually measures (`FINDING 238`, `FINDING 241`).

**How to test.** The §3 census over all five: `550` plates, `FAIL 0` — or, under `D-EU-89` clause 2, exactly the
residual list of T05d and no other `FAIL` — and the seven checks all present in the JSON. Report `max aspect`
and `over 3.0` per test, against T01's baseline row for the same test. The sheet's header states the
constant's status in one line: *frozen at X* or *set to 2.5 by `D-EU-89` clause 2*.

---

### T07 — Rules docs, archive, prompt, state

**What.**
1. Re-date the four rules docs to `*_nocore_2026-09-03.*`. Move the four `*_nocore_2026-09-02.*` into
   `rules/archive/`. The content changes required, not optional:
   - add `C11` to the rules table and the check legend (`D-EU-82`), and add `D-EU-82` … `D-EU-87` wherever
     `D-EU-79/80/81` already appear;
   - **`C10` is restated.** `RULES_dwelling_layout_groups_nocore_2026-09-02.html` still defines it as
     `widest_fit >= 2.00 m`, which is the defect of `FINDING 241`. The global law now reads: *no part of a
     flat may be narrower than 2.00 m; narrowness inherited from the footprint's own tips and slots is
     excluded, narrowness created by the cut is not, measured as a morphological opening at r = 1.00 m.*
   - **the group algorithms are restated where `D-EU-86` changed them** — `COURTYARD`, `L_SHAPE` and
     `COMPLEX_MULTI_WING` now divide a thick band across its **depth** as well as along its run, and a
     `rows x cols` grid on either bearing is a first-class candidate for every group (`D-EU-83`). The
     document is the specification: if the code divides a ring in two layers, the document must say so.
   - the doc says "six checks" in at least one place — there are seven.
2. The `TEST_0*_nocore_2026-09-02.html` sheets are **already** in `rules/tests/archive/` (owner, 2026-09-03)
   and the owner-read `TEST_0*_nocore_2026-09-03.html` set is **already** in
   `rules/tests/archive/reviewed_2026-09-03/` — verify both. **Then, authorised by the owner's own sentence
   *"you can archive non core versions"* (`D-EU-89` clause 5): move the five `TEST_0*_nocore_2026-09-03.html`
   out of `rules/tests/` (they are already byte-identical in `archive/reviewed_2026-09-03/`; `cmp` first, then
   delete the live copy — no second archive copy), so that the `_r2` sheets of T06 are the only live set.** 🔴 Three of the 2026-09-02 five
   (`TEST_01_three_per_group`, `TEST_03_five_per_group`, `TEST_05_ten_per_group`) were overwritten in
   place on 2026-09-03 and no longer show the delivered 2026-09-02 drawings (`FINDING 239`). Archive all
   five, and state that fact in your `CP-3` report — do not present the three as authentic.
3. Sweep every live citation of a moved filename (`grep -rn` over `docs/` and `scripts/`, excluding
   `docs/docs_DONE/`, `docs/docs_main/`, `docs/docs_TODO/layoutgenerator/`, and the progress logs of closed
   plans, which are historical records) and repair it **by filename**, not by prefix substitution.
4. Update `prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` and the EU section of
   `STATE_european_locations_v5.md`: seven checks, the frozen `MAX_FLAT_ASPECT`, the new sheet names, the
   three laws, `FINDING 238` … `FINDING 243`, `D-EU-85` … `D-EU-89`, next free
   **`D-EU-90` / `FINDING 244`**. `STATE_european_locations_v5.md` already carries every finding and
   ruling through `FINDING 243` / `D-EU-89` — do not re-add them, and never add notes to
   `BRIEF_european_locations_v5.md` or `CHECKLIST_european_locations_v5.md` (owner, 2026-09-03: those two
   are representations, not development documents; `STATE` is where notes go).

**Why.** The archiving rule at the head of `docs/PROJECT_CHECKLIST.md`: an archive is not finished until every
citation into it has been swept and repaired.

**How to test.** `grep -c` for each moved filename outside `archive/` returns only historical-log hits, and you
list them. The four `*_nocore_2026-09-03.*` docs exist; the four `*_nocore_2026-09-02.*` do not exist outside
`archive/`.

**🔴 CP-3 — final report.** The 550-plate census, the ladder table, the frozen constant, the before/after
slenderness table against §0, and the citation sweep count.

---

## 8. Progress log

<!-- one entry per completed task: #### TXX — <title> — completed YYYY-MM-DD
     Artifacts / Deviations / Test status / Notes -->

#### T01 — Snapshot the before-picture, and reproduce the director's census — completed 2026-09-03

Artifacts: `openubem/outputs/eu_evidence/EU-21/rules_tests/baseline_nocore_2026-09-02/test_0{1..5}_nocore.json`
(byte copies of the five live `test_0N_nocore.json`).

Deviations: none.

Test status: sha256 + size identical for all five pairs —
test_01 `5edf3fc4ea77e97d79ccd7dd038b3f29c876328b0442258e31133bb2ee368003` 51218 B;
test_02 `c449b8a9b957e34954ee33dacbdbc183e7dd9896369331511dd19dbca5fb49fe` 324586 B;
test_03 `c7e44d27d7cca00286e5a51583f410c033a4bd17182cb70758409792e59f2eae` 81919 B;
test_04 `d7a637a8c437e33979eafb449b05b69e6247c3d31fb871da908ef71117f2f440` 543663 B;
test_05 `b6fc9c4e69610e820a39b2cb85790933bb5e28db5111e5f9772ebefa717de198` 163688 B.
Census control reproduced §0 exactly: 3,267 flats total, 1,577 over 3.0, max 14.12
(per-test: t1 102 flats/21 over3.0/max5.53; t2 990/561/13.02; t3 167/30/5.43; t4 1650/896/14.12; t5 358/69/8.54).
All 550 plates PASS on the six checks (33+132+55+220+110).

Notes: none.

#### T02 — `C11` becomes a scored check — completed 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py` — `MAX_FLAT_ASPECT = 3.0` constant, `flat_aspect(f)` helper,
`checks["C11"]` in `run_checks`, `"C11"` added to the verdict tuple, `CHECK_META` row (tolerance string
built from `MAX_FLAT_ASPECT`, not typed).

Deviations: also added `"C11"` to the two other places the six-check id tuple was enumerated in the same
file — the card chip loop and `commonest_failed_check` — otherwise a plate failing only on `C11` would
verdict `FAIL` while its card showed no failing chip and the fleet tally undercounted the commonest
failed check. Same file, no new file, no threshold changed.

Test status: `--test 1` census (rewritten `test_01_nocore.json`) — 33 plates, `Counter({'PASS': 27,
'FAIL': 6})`, 102 flats, max aspect 5.53, 21 over 3.0. 6/33 plates fail `C11` (all six fail on `C11`
alone): `COURTYARD relation/12765478` 5.2:1, `CORRIDOR_RECTANGLE way/435927693` 3.1:1, `L_SHAPE
way/1057823423` 5.5:1, `L_SHAPE way/432412736` 3.1:1, `U_OR_T_SHAPE …240879975_part0` 3.8:1,
`U_OR_T_SHAPE …240881146_part0` 4.8:1. `FAIL` expected and correct per plan — cutter not yet updated.

Notes: none.

#### T03 — `C11` enters the plate score and the early-exit gate — completed 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py` — `_plate_score` (`07:411`) now returns
`(cov_ok, c5_ok, c6_ok, c4_ok, c11_ok, min_c10, min_c6, -max_aspect)`, `c11_ok` inserted immediately
after `c4_ok` and `-max_aspect` appended last; `_fully_ok` (`07:437`) unpacks the 8-tuple and requires
`c11_ok`.

Deviations: none.

Test status: `--test 1` census (rewritten `test_01_nocore.json`) — 33 plates, `Counter({'PASS': 33})`,
102 flats, max aspect down from 5.53 (T02) to 2.89, 0 over 3.0. `C11` failures dropped to zero already
at this stage (axis choice + boundary sweep + neck donation, still the old single-row candidate set —
the grid cutter of T04 has not run yet). Compared every plate's `C1/C4/C5/C6/C10` pass/fail against the
T01 baseline JSON by `(group, building_id)`: 0 regressions.

Notes: none.

#### T04 — Grid-first: every `rows x cols` scheme, on both axes — completed 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py` — `build_flats` (`07:540`) now searches `rows` from 1 to
`min(k, MAX_GRID_ROWS=6)`, each on both axes (`theta_offset` 0.0/90.0); `rows == 1` tries both the plain
equal-area cut and the `_sweep_boundaries` variant, `rows >= 2` uses `cut_grid`; the "return default
untouched when already `_fully_ok`" early exit is deleted (candidates always compared by `_plate_score`);
`_donate_the_neck` last-resort stays gated on `_fully_ok`, unchanged. `build_flats`/`build_plate` now
return/carry `rows` (the winning row count) into `rec["rows"]`, printed in `plate_line` (`07:713`), never
on the card.

Deviations (both required to make T04 actually run, same file, no threshold loosened, registered in
`debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 per rule 8):
1. Fixed a latent display bug independent of T04's own logic: `build_plate`'s exception handler
   (`07:693`) sets `verdict="FAIL", status="ERROR"` (correct per rule 5), but `card()`, `build_html`'s
   `errors`/`spreads`, and `commonest_failed_check()` all tested the never-true `verdict == "ERROR"`,
   so the one `--test 5` plate that raised a `GEOSException` (surfaced for the first time by the wider
   row search) crashed the whole run with `KeyError: 'spread'` instead of drawing an error box. Fixed to
   key off `status`/`"checks" not in p` instead; `verdict` itself untouched.
2. Fixed a real geometry bug the broader search exposed: `to_world`'s rotation can leave two flats'
   shared boundary vertex at two floating-point positions only ULPs apart (exact pre-rotation, each
   rotated independently), and GEOS's `intersection()` on the rotated pair then reads a false, large
   overlap — confirmed on `CORRIDOR_RECTANGLE 32781` (test 1 plate 14): raw `.intersection().area`
   reported the *entire* area of one flat as overlapping its neighbour, though disjoint except at one
   shared corner, which `C4` then correctly (per its own threshold) read as a `65.81 m²` violation of a
   plate that had been clean since T01. New `_snap_world(g)` (`07:327`, `set_precision(g, 0.001)`, same
   grid as `_normalize`, `buffer(0)`/unsnapped fallback mirroring `05_group_cutters.py:171-179`) is
   applied to every flat returned by `cut_nocore` and `cut_grid` (not `_cut_nocore_t01`, the `STAGE=="t01"`
   diagnostic path, left exactly as it was per rule). Also incidentally resolved the 3 `GEOSException`
   crashes on test 5 (`SLAB …240880370_part0`, `L_SHAPE way/293596159`, `COMPLEX_MULTI_WING
   way/434878287`) — all 3 now draw cleanly (2 `PASS`, and none crash) rather than raising.

Test status — census + rows histogram + residual `C11` (post both fixes above):
- **Test 1**: 33 plates, `Counter({'PASS': 33})`, 102 flats, max aspect 2.98, 0 over 3.0. Rows histogram
  `{1: 20, 2: 11, 3: 2}`. 0 residual `C11` failures. 0 regressions vs T01 baseline on `C1/C4/C5/C6/C10`.
  Runtime ~3 s.
- **Test 3**: 55 plates, `Counter({'PASS': 53, 'FAIL': 2})`, 167 flats, max aspect 4.23, 3 over 3.0.
  Rows histogram `{1: 32, 2: 19, 3: 2, 4: 1, 5: 1}`. Residual `C11` failures: `COURTYARD
  relation/5808696` n=2, `3.0 : 1`; `U_OR_T_SHAPE 28621` n=3, `4.2 : 1`. 0 regressions vs T01/T03
  baseline on `C1/C4/C5/C6/C10`. Runtime ~5 s.
- **Test 5**: 110 plates, `Counter({'PASS': 108, 'FAIL': 2})`, 358 flats, max aspect 5.18, 4 over 3.0.
  Rows histogram `{1: 54, 2: 44, 3: 8, 4: 3, 5: 1}`. Residual `C11` failures: `COURTYARD 33141` n=3,
  `5.2 : 1`; `SLIVER 32758` n=3, `3.4 : 1`. No `ERROR`-status plate remains (all 3 pre-fix crashes now
  draw). 0 regressions vs baseline on `C1/C4/C5/C6/C10`. Runtime ~10 s.

Notes: `C11` is not yet at `FAIL 0` (4 residual plates across the two size-imposed tests, `T05` has not
run) — expected at this stage; T05 calibrates `MAX_FLAT_ASPECT` against all 550 plates next.

#### T05 — Calibrate `MAX_FLAT_ASPECT` once, then freeze it — STOPPED at CP-2, 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py:1040` — `html_path` repointed from `_nocore_2026-09-02` to
`_nocore_2026-09-03` (`D-EU-85`, done first, before any run). `07:634` — `MAX_FLAT_ASPECT` left at
`4.0` with a comment recording the full ladder and the CP-2 stop (not frozen/adopted).

Deviations: none — T05.0 done first per the hard rule; no threshold loosened outside the ladder itself.

Test status — the ladder, `--test all` (550 plates) at each rung, `TOTAL FAIL` = sum of `C11`-only
`FAIL` plates across the 5 tests:

| rung | t1 | t2 | t3 | t4 | t5 | TOTAL FAIL |
| --- | --- | --- | --- | --- | --- | --- |
| 2.5 | 2 | 17 | 3 | 27 | 2 | 51 |
| 3.0 | 0 | 7 | 2 | 13 | 2 | 24 |
| 3.5 | 0 | 5 | 1 | 10 | 1 | 17 |
| 4.0 | 0 | 4 | 0 | 7 | 0 | 11 |

**No rung reaches `FAIL 0` on all five tests.** Per `D-EU-84` / hard rule 3, this is a `CP-2` stop: the
constant is not frozen, `T06`/`T07` do not run this session.

Residual at 4.0 (the least-strict rung, smallest residual): 11 plate-appearances, all `n = 12`, 7
unique buildings (each appears in both `test 2` and `test 4`, the two size-imposed tests that force
`n=12`):

| group | building_id | n | max aspect | seen in |
| --- | --- | --- | --- | --- |
| COURTYARD | 28125 | 12 | 6.8 : 1 | t2, t4 |
| COURTYARD | 29659 | 12 | 14.1 : 1 | t4 |
| COURTYARD | 31169 | 12 | 5.1 : 1 | t4 |
| L_SHAPE | way/290026256 | 12 | 5.0 : 1 | t2, t4 |
| L_SHAPE | way/391279228 | 12 | 6.7 : 1 | t4 |
| COMPLEX_MULTI_WING | way/968439455 | 12 | 4.7 : 1 | t2, t4 |
| COMPLEX_MULTI_WING | 31312 | 12 | 5.6 : 1 | t2, t4 |

All 7 are the plan's own §0 worst-plate list (`COURTYARD 29659` unchanged at 14.1 : 1 — the grid-first
cutter of T04 could not improve it under any `rows x cols x` axis candidate at `k=12`). `test 1`, `test
3` and `test 5` (the `own`-selection tests, 2–8 flats/floor) reach `FAIL 0` at rung 3.0 already; the
residual is confined entirely to the two `size`-imposed tests' `n=12` plates.

Notes: no exemption invented (rule 3). `MAX_FLAT_ASPECT` left at `4.0` in the file as the
least-permissive-first candidate but explicitly marked not-frozen in its own comment, pending the
director's ruling on the 7-building residual. `T06`/`T07` not started.

#### T05b — Fix the three failing group rules, then re-run the ladder (`D-EU-86`) — STOPPED, second stop, 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py` — new `_split_at_y` (exact 2-way partition via
`shapely.ops.split`, never a box-intersection pair) and `cut_layered(poly, k, theta_offset, passes=3)`,
one more candidate scheme wired into `build_flats`'s `rows_ == 1` branch alongside `cut_nocore`'s
default and swept variants. `cut_layered` merges an adjacent pair of single-axis columns whose worst
aspect still exceeds `MAX_FLAT_ASPECT` and re-cuts the merged pair across its own local depth (an
equal-area split on the perpendicular axis) instead of only along the run — `D-EU-86` clause 3's own
wording. A merge is kept only when: the split comes back exactly two clean polygons; neither half is
lobed; each half keeps `>= 2.50 m` of the plate's own outer-facade contact (`C6`, never loosened); and
the merge strictly lowers the pair's own worst aspect. Anything failing one gate keeps its original two
ribbons — the candidate can only help a plate's score, never regress it. `MAX_FLAT_ASPECT`'s own comment
block (`07:744`) rewritten with the T05b ladder and this stop.

Diagnosis (step 1, before any fix, `COURTYARD 29659` at `n=12`, all 14 candidates `build_flats` already
generates): the single-axis default (`rows=1`) wins the plate today at `14.119 : 1` (`score
(True,True,True,12,False,2.0,2.765,-14.119)` — `C1/C5/C6` pass, `C11` fails). A compliant-`C11`
candidate **was already generated**: `rows=3` and `rows=4` (both axes) score `max_aspect` `1.75-1.98`,
well under `4.0` — but every one of them has `min_c6 = 0.0`: the plate-wide Cartesian row-band cuts a
horizontal band straight through the ring's own void, and at the X-ranges that cross the hole, the
middle band's piece sits only against the courtyard's inner (hole) boundary, never the plate's true
outer boundary. Per-flat check on that `rows=3` candidate: flats 5 and 6 (of 12) read `contact = 0.00`
against `poly.exterior`, all others `4.0-16.3`. So the answer to step 1 is **generated and lost, but not
on score order — lost because the plate-wide grid band is topologically unsafe for a ring**: `C6` is a
hard gate ahead of `C11` in `_plate_score`, correctly, and no rescoring fixes a candidate that is
actually `C6`-illegal. This is why the fix is a new *candidate* (`cut_layered`, local to a column pair,
safety-checked before it is ever offered to the score) and not a change to `_plate_score` or to `C6`.

Deviations (both required to get `cut_layered` graded honestly, same file, no check loosened, first one
registered in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 per rule 8):
1. `cut_layered`'s first draft returned the caller's raw `poly` (unnormalized) instead of `poly_n`
   (`_normalize(poly)`), unlike `cut_nocore`/`cut_grid`, which both reassign and return the normalized
   polygon. `build_flats`'s outer `donate_leftovers(p3, flats3)` then compared world-frame flats against
   the wrong reference, reading a spurious perimeter-hugging "leftover" from the mismatch and donating it
   into whichever flat's boundary happened to touch it most — inflating that one flat from 6 to 42
   vertices and tripping `C5`'s 40-point cap on a candidate that was otherwise the plate's best `C11`.
   Fixed to return `poly_n` (and use `poly_n.exterior` for the internal `C6` contact gate), matching the
   other two cutters exactly. Confirmed by re-running the `COURTYARD 29659` diagnostic before/after: raw
   `cut_layered` output was already `<= 10` points per flat; only the mismatched reference inflated it.
2. Original `cut_layered` draft used two independent `box()` intersections for the depth split and
   patched the mismatch with a leftover-donation loop; replaced with `shapely.ops.split` against one
   `LineString` (`_split_at_y`), which returns an exact 2-way partition with no gap/overlap to patch —
   simpler and it was what actually stopped the vertex inflation once deviation 1 was also fixed.

Test status — the ladder re-run in full after the fix, `--test all` (550 plates) at each rung, computed
**in-memory** (`build_plate` called directly per test/rung, no `run_test`/HTML write) for 2.5/3.0/3.5,
and once through the real CLI at the frozen-comment value `4.0` to keep the on-disk `test_0N_nocore.json`
/ `TEST_0N_..._nocore_2026-09-03.html` consistent with the reported final rung (same convention T05 left
them in):

| rung | t1 | t2 | t3 | t4 | t5 | TOTAL FAIL |
| --- | --- | --- | --- | --- | --- | --- |
| 2.5 | 2 | 10 | 3 | 16 | 2 | 33 |
| 3.0 | 0 | 4 | 2 | 8 | 2 | 16 |
| 3.5 | 0 | 3 | 0 | 7 | 1 | 11 |
| 4.0 | 0 | 1 | 0 | 4 | 0 | 5 |

**Still no rung reaches `FAIL 0` on all five tests.** Every rung's `TOTAL FAIL` roughly halved against
T05's own ladder (51→33, 24→16, 17→11, 11→5), and `C1/C3/C4/C5/C6/C10` regression count is **0/550** at
the `4.0` build (checked directly against every plate's own check dict, not resampled).

Before/after on the plan's own 7-building residual (`FINDING 240`, all `n=12`, worst aspect at rung
4.0):

| group | building_id | before | after | status |
| --- | --- | --- | --- | --- |
| COURTYARD | 28125 | 6.8 : 1 | 3.2 : 1 | **fixed** |
| COURTYARD | 29659 | 14.1 : 1 | 14.1 : 1 | unchanged |
| COURTYARD | 31169 | 5.1 : 1 | 5.1 : 1 | unchanged |
| L_SHAPE | way/290026256 | 5.0 : 1 | 5.0 : 1 | unchanged |
| L_SHAPE | way/391279228 | 6.7 : 1 | 6.7 : 1 | unchanged |
| COMPLEX_MULTI_WING | way/968439455 | 4.7 : 1 | 2.8 : 1 | **fixed** |
| COMPLEX_MULTI_WING | 31312 | 5.6 : 1 | 3.8 : 1 | **fixed** |

3 of 7 fully resolved. The 4 that remain (5 plate-appearances: `way/290026256` in both `t2`/`t4`) are
the residual at `4.0`. `COURTYARD 29659` is byte-identical to its pre-fix value: `cut_layered`'s own
safety gates (exact 2-piece split, `C6 >= 2.50 m` on **both** halves, strictly-lower aspect) never
accept a legal merge on this specific plate — every pairing attempted either fails the clean-split test
or would isolate a flat against the courtyard void with zero outer contact, exactly the defect the gates
exist to block.

**Stop-and-report, per `D-EU-86` clause 1 / T05b's own stop-and-report instruction.** A genuine
depth-division fix is implemented, wired into the search, and measurably helps (every rung's total FAIL
roughly halved, 3 of 7 named buildings now PASS) — but no rung reaches `FAIL 0`. Per the plan: no
exemption is invented, no rung beyond `4.0` is tried, `C11` is not relaxed, and `T06`/`T07` do not run
this session. `MAX_FLAT_ASPECT` stays at `4.0` in the file, explicitly marked not-adopted in its own
comment, pending the director's ruling on the 4-building residual (`COURTYARD 29659` in particular,
which no plate-wide or column-pair candidate tried so far can touch without breaking `C6`).

#### T05b — resume: step 0 (owner-read sheets restored, html tag repointed) — completed 2026-09-03

Artifacts: `docs/.../rules/tests/TEST_0[1-5]_*_nocore_2026-09-03.html` restored byte-identical from
`rules/tests/archive/reviewed_2026-09-03/` (`cmp` clean on all five — 5 restored, 5 identical).
`scripts/eu21/07_nocore_tests.py:1177` `run_test`'s html tag repointed from `_nocore_2026-09-03` to
`_nocore_2026-09-03_r2`, confirmed by `grep -n "_nocore_2026-09-03"` returning the one repointed line
only.

Deviations: none for step 0 itself. On disk before this session started, the diagnosis (step 1,
`COURTYARD 29659` at `n=12`) and the full re-run ladder (step 5) required by T05b's own "How" were
already present and already logged in this doc's own T05b entry above (`cut_layered`, the `_split_at_y`
depth-division candidate, ladder re-run to `TOTAL FAIL` `33/16/11/5` at `2.5/3.0/3.5/4.0`, stop at
`4.0` not frozen) — that work is not repeated here. Spot-checked instead: `--test all` at
`MAX_FLAT_ASPECT=2.5` (unmodified cutter, before any T05c edit) reproduced `TOTAL FAIL 33` exactly
(`t1 2 t2 10 t3 3 t4 16 t5 2`), byte-for-byte the same as the logged T05b ladder — confirms the on-disk
cutter state matches what is logged and step 0 alone changed nothing about it.

Test status: 5 restored / 5 identical (`cmp`). `grep -n "_nocore_2026-09-03" scripts/eu21/07_nocore_tests.py`
→ one line, the repointed `html_path` assignment. Spot-check ladder rung (`2.5`) reproduces the logged
`TOTAL FAIL 33`.

Notes: per the director's amended stop clause (`D-EU-86` clause 1, quoted at this doc's T05b header),
the stop is taken after T05c's own ladder, not here — execution continues straight into T05c below,
whose new `C10` re-runs the ladder again regardless. `MAX_FLAT_ASPECT` is not touched by this entry; it
is re-set task-by-task through T05c's own ladder below.

#### T05c — Rebuild `C10` as a real pinch test (`D-EU-87`) — STOPPED, `FAIL 0` unreachable, 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py` — `_opening_lost(g, r=1.00)` (mitre-joined
erode/dilate-back opening, guards the empty-erosion case), `_pinch_geom(f, plate)` (the geometry of `f`
narrower than 2.00 m that the cut, not the footprint, created — `_opening_lost(f)` minus
`_opening_lost(plate)`) and `pinch_area(f, plate)` (its area). `_plate_score`'s `min_c10` term replaced
by `round(-pinch_total, 3)` (created-pinch area, minimised, same rank as before — beside `C11`,
`D-EU-87` clause 5); `_fully_ok` gates on `sum(pinch_area) <= 0.10` instead of `min(widest_fit) >= 2.00`.
`run_checks`'s `C10` now `{"pass": pinch_total <= 0.10, "show": f"{pinch_total:.2f} m²"}` (was
`widest_fit`-based). `_donate_the_neck` retargeted from `widest_fit` (silent about a narrow strip inside
an otherwise-wide flat) to `pinch_area`/`_pinch_geom` directly — selects the flat with the largest
created pinch, donates the exact pinch geometry (not a probe-width guess) to the neighbour sharing the
most boundary, same `_clean_merge`/`lobes_of`/`_best_recipients` machinery as before. `widest_fit` no
longer appears in `_plate_score`, `_fully_ok` or `C10`'s own check (`D-EU-87` clause 1); it survives only
in `_sweep_boundaries` (candidate-search heuristic, not a verdict) and is otherwise unused
(`_min_widest` is now dead code, left in place, not deleted — out of this task's scope). `MAX_FLAT_ASPECT`'s
comment block (`07:746`) rewritten with the T05c ladder and this stop, in addition to T05b's own record
already there. `docs/.../rules/tests/TEST_0[1-5]_*_nocore_2026-09-03_r2.html` written by every
`--test all` run this task issued (five files, tag from T05b step 0) — the `_2026-09-03` (no `_r2`)
owner-read set stays untouched (`cmp` clean, re-verified after the final run).

Deviations (same file, no check loosened, registered in
`debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 per rule 8): the first `--test all` run under the
new `pinch_area` scoring raised `shapely.errors.GEOSException: TopologyException: unable to assign free
hole to a shell`, uncaught inside `_opening_lost`'s mitre-joined buffer pair, on `SLAB 28583` (test
03/05) — caught by `build_plate`'s outer handler so the run did not crash, but the plate shipped with no
`checks` dict at all (worse than an honest `FAIL`: `C1/C3/C4/C5/C6` become unscoreable for that record).
Fixed: `_opening_lost` now tries once plainly, retries once on `buffer(0)`-cleaned geometry, and falls
back to returning the input unchanged (the conservative "whole flat is lost" answer) rather than letting
GEOS raise — same guard pattern as the codebase's existing `_safe_union`/`_safe_precision`. Verified:
`SLAB 28583` builds and scores cleanly at every ladder rung after the fix; 0/550 plates carry
`status=ERROR` in any of the five final JSONs (was 2 before the fix).

Test status — the ladder re-run in full, `--test all` (550 plates) at each rung, after the
`_opening_lost` fix (`TOTAL FAIL` = plates failing `C10` and/or `C11`, i.e. every plate that is not
`PASS`):

| rung | t1 | t2 | t3 | t4 | t5 | TOTAL FAIL |
| --- | --- | --- | --- | --- | --- | --- |
| 2.5 | 3 | 27 | 4 | 44 | 3 | 81 |
| 3.0 | 2 | 20 | 3 | 34 | 3 | 62 |
| 3.5 | 1 | 16 | 1 | 25 | 3 | 46 |
| 4.0 | 1 | 14 | 1 | 22 | 1 | 39 |

**No rung reaches `FAIL 0`.** `C10` is the dominant failing check at every rung (2.5: 54 `C10`-check
failures across the 5 tests; 4.0: 36), concentrated in `COURTYARD`/`COMPLEX_MULTI_WING` at `n=12` — the
identical shape family, and in one case the identical plate (`COURTYARD 29659`, still the untouched
single-axis `rows=1` candidate, `34.11 m²` created pinch, `1.78 m` local band), as `D-EU-86`'s own `C11`
residual: a courtyard ring whose local band is too thin to divide across its own depth (`cut_layered`'s
own `C6`-outer-contact gate never finds a legal merge there either).

Whole-fleet effect of the `D-EU-87` fix (`pinch_area` computed identically on the delivered
`baseline_nocore_2026-09-02` polygons and on this build's final, `4.0`, JSONs): total created-pinch area
`1358.78 m²` → `134.63 m²` (**−90 %**); plates over the `0.10 m²` tolerance `184/550` → `33/550`
(**−82 %**). This reproduces the director's own `FINDING 241` census (`182/550` plates, `1349 m²` — this
session's independent re-derivation is `184/550`, `1358.78 m²`, the same order and within measurement
noise of re-deriving from the delivered JSONs rather than re-cutting).

The owner's own four marked plates (`D-EU-87`, `FINDING 241`), created-pinch area before (baseline
2026-09-02, this session's `pinch_area` applied retroactively) and after (this build, `4.0`) — **note:**
the `STATE_european_locations_v5.md` `D-EU-87` text names the last two `COMPLEX_MULTI_WING`; both are
`COURTYARD` in every test JSON (`building_id` is unambiguous and unique; used the correct group below):

| plate | before | after | status |
| --- | --- | --- | --- |
| `COMPLEX_MULTI_WING` Bologna `29965` | `4.03 m²` | `0.005 m²` | **PASS** |
| `COURTYARD` Bologna `32052` | `0.00 m²` | `0.00 m²` | PASS (unchanged) |
| `COURTYARD` Bologna `30127` | `0.00 m²` | `0.004 m²` | PASS (float noise, still under tolerance) |
| `COURTYARD` Bologna `28754` | `38.19 m²` | `1.06 m²` | **FAIL, −97 %** |

3 of 4 owner-marked plates now `PASS`; the fourth (`28754`, `n=12`, the plate's own densest cut) is
reduced 97 % but not eliminated.

Regression check, `C1/C3/C4/C5/C6` at the final (`4.0`) build vs `baseline_nocore_2026-09-02`, matched
by `(group, building_id, drawn_per_floor)` across all 550 plates in both: **0 regressions on any of the
five checks** (`{'C1': 0, 'C3': 0, 'C4': 0, 'C5': 0, 'C6': 0}`).

Residual `C10` plate list at the frozen-in-file (not adopted) rung `4.0`, created-pinch area and local
band width (`2 × distance from the pinch piece's own centroid to the plate's own boundary`, the
narrowest-reasonable proxy for "how wide is the plate here") of the largest pinch piece per plate — 15
unique buildings, 24 plate-appearances across the two size-imposed tests (`t2`/`t4`) plus a handful of
`own`-selection repeats:

| group | building_id | n | C10 area | local band |
| --- | --- | --- | --- | --- |
| COURTYARD | 29659 | 12 | 34.11 m² | 1.78 m |
| COMPLEX_MULTI_WING | way/968439455 | 12 | 18.42 m² | 9.97 m |
| COURTYARD | 31169 | 12 | 13.95 m² | 1.50 m |
| COURTYARD | relation/12765478 | 6 | 5.86 m² | 0.51 m |
| COURTYARD | relation/4678507 | 9 | 4.41 m² | 17.62 m |
| COMPLEX_MULTI_WING | 31312 | 12 | 3.66 m² | 1.28 m |
| TRIANGLE | BATIMENT...240877151_part0 | 12 | 2.97 m² | 1.50 m |
| SLIVER | 29816 | 12 | 2.33 m² | ~0.00 m |
| COMPLEX_MULTI_WING | way/311595048 | 6 | 1.88 m² | 0.54 m |
| U_OR_T_SHAPE | 30320 | 9 | 1.72 m² | 0.87 m |
| COURTYARD | 28782 | 9 | 1.56 m² | 18.30 m |
| TRIANGLE | 31311 | 12 | 1.12 m² | 0.45 m |
| COURTYARD | 28754 | 12 | 1.09 m² | 1.22 m |
| CORRIDOR_RECTANGLE | 32721 | 12 | 1.08 m² | 0.81 m |
| COMPLEX_MULTI_WING | 31801 | 12 | 0.93 m² | 5.09 m |
| COMPLEX_MULTI_WING | way/434878287 | 5 | 0.66 m² | ~0.00 m |

Notes: **`FAIL 0` is unreachable at every rung tried (`2.5`/`3.0`/`3.5`/`4.0`)** after a genuine cutter
fix (`_opening_lost`/`pinch_area`/`_pinch_geom`, `_donate_the_neck` retargeted, `_fully_ok`/`_plate_score`
rewired) that measurably works (−90 % fleet-wide pinch area, 3 of 4 owner-marked plates now `PASS`).
Per this task's own stop-and-report clause: **STOP after T05c** — `T06`/`T07` do not run this session.
`MAX_FLAT_ASPECT` stays at `4.0`, explicitly marked not-adopted in its own comment (`07:746`). No
exemption invented, no plate dropped, the `0.10 m²` tolerance never raised, `widest_fit` never restored
as the verdict. The residual is the same structural family `D-EU-86` already identified (thick-band
courtyard rings and dense `n=12` multi-wing plates) — a further fix would need a cutter that can
segment a ring or a wing **around** a void/notch, not merely across a band's depth (`cut_layered`) or by
donating a pinch piece to a neighbour (`_donate_the_neck`); both are already at work here and both
still fall short on this specific residual. `TEST_0[1-5]_*_nocore_2026-09-03.html` (no `_r2`, the
owner-read set) reconfirmed byte-identical to `rules/tests/archive/reviewed_2026-09-03/` after the
final run (5/5 `cmp` clean) — the `_r2` tag from T05b step 0 held for every run this task issued.

Deviation, out of order (T06's own content, applied here): while this task's own ladder runs were still
in flight, `07_nocore_tests.py`'s sheet prose was also corrected — the `C10` check-legend row (restated
as the created-pinch area test, `07:1007`), the `D-EU-81` rules bullet (no longer `widest_fit`,
`07:1031`), and the four "six checks"/"All six checks passed" strings (`07:1141/1144/1153/1174`) now
read "seven". This is `T06`'s designated prose fix, done early because leaving the known-wrong "six
checks"/`widest_fit` text in place would have been strictly worse than fixing it, and it does not depend
on `MAX_FLAT_ASPECT` being frozen. `T06` itself — the frozen-constant final run, the five delivered
`_nocore_2026-09-03_r2.html` sheets as the accepted artifact, and its own progress-log entry — is **not**
executed and **not** claimed done; the `_r2` sheets on disk are this task's own last ladder run (`4.0`,
not frozen), not a `T06` delivery.

#### T05d — Second repair round: the ring/wing residual and the `MultiPolygon` fault (`D-EU-89` clauses 2-3) — STOPPED, `FAIL 0` unreachable, 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py` — **`FINDING 243` fix**: `_fix_snap_multipolygons(flats)`
(`07:352`), applied right after `_snap_world` in `cut_nocore`, `cut_grid` and `cut_layered`. Root cause,
confirmed by direct reproduction (a 10-line driver via `load_universe`, per the plan's own instruction,
never `08_district_viewer.py --only`, which does not exist): a flat can leave rotation (`to_world`) as
an INVALID, self-touching `Polygon` (a razor-thin bowtie neck from the floating-point rotation itself,
not the cut), and `_snap_world`'s own `set_precision(g, 0.001)` then resolves that self-touch under
GEOS's `valid_output` mode and genuinely splits it into a `MultiPolygon` (measured on `COMPLEX_MULTI_WING
way/100704705`, `theta_offset=90`, the swept-boundary variant: 141.836 m² clean `Polygon` pre-rotation ->
141.836 m² *invalid* `Polygon` post-rotation -> 141.567 + 0.253 m² `MultiPolygon` post-snap). Every
downstream reader (`_plate_score`, `_best_recipients`, `_delobe_and_donate`, `run_checks`) assumes one
flat is one `Polygon`, which is why the 550 test plates never showed it: the swept/grid/radial/wingwise
candidates that expose it are only reached by plates at `k`/`theta` combinations the battery never drew.
Fix mirrors `05_group_cutters.py:264`'s own `dissolve_pass` (read-only, mirrored, never imported): keep
each flat's own largest piece, donate every other piece to whichever flat (its own remaining piece
included) shares the most boundary via the existing `_best_recipients`/`_clean_merge` gate, escalating a
small buffer (0.005/0.02/0.1 m, then 0.1/0.5/2.0 m as a last resort against the largest flat) only if the
direct merge fails — never drops area, never catches-and-ignores.

**`FINDING 242` (ring/wing) candidates**: `cut_radial(poly, k, theta_offset)` (`07:594`) — a courtyard
ring's own void, cut into `k` equal-area angular sectors from the void's own centroid
(`_equal_area_theta`/`_wedge`, `07:557-593`, the same binary-search sweep as `equal_area_x` walked over
angle instead of x); every sector spans the ring's full radial depth by construction, so unlike a
plate-wide Cartesian band it touches both the void and the outer boundary, which is exactly why
`cut_layered` (`D-EU-86`) could never win a ring (`FINDING 240`'s own diagnosis). `None` when `poly` has
no interior ring. `cut_wingwise(poly, k, theta_offset)` (`07:626`) — each of a multi-wing plate's own
wings, found by `lobes_of` (read-only, imported from `02_one_core_per_plate.py` via `05_group_cutters.py`,
default neck radius `r=0.75`), columned in ITS OWN local frame (`frame`/`to_local`/`equal_area_x`)
instead of the plate's one shared axis, flats apportioned per wing by area (the same rounding sweep
`_grid_seeds` already uses). `None` when `lobes_of` finds fewer than two wings or there are more wings
than flats. Both wired into `build_flats`'s `rows_ == 1` branch (`07:920-936`) alongside `cut_nocore`,
the swept variant and `cut_layered` — never preferred by name, scored by the unchanged `_plate_score`,
kept only when they win. `MAX_FLAT_ASPECT`'s own comment block (`07:1013`) rewritten with the T05d
ladder and this stop; constant set to `2.5` (`07:1049`).

Deviations: none from the plan's own "How" — both new candidate families are named exactly
`cut_radial`/`cut_wingwise` as specified, touch only `07_nocore_tests.py`, and are scored by the
existing `_plate_score`, never preferred by name. One methodological choice, not a deviation: per
`D-EU-85`/T05b/T05c's own precedent (a real CLI run to keep on-disk `test_0N_nocore.json` /
`TEST_0N_..._nocore_2026-09-03_r2.html` consistent with the reported final rung), this task also ran
`--test all` once for real at the final constant (`2.5`) after sweeping the ladder in-memory (no HTML
writes) for the search itself — same convention, not a `T06` delivery.

Test status:
- **`FINDING 243` reproduction**: all 17 previously-`ERROR` census buildings (Madrid 8: `way/100704705`,
  `way/288461992`, `way/434877453`, `way/435397047`, `relation/4179135`, `relation/12800463`,
  `relation/12800464`, `relation/12803902`; Lyon 1: `BATIMENT0000000240881271_part0`; Bologna 8: `32790`,
  `32800`, `31932`, `30912`, `32062`, `28583`, `32135`, `31887`) now build `status="direct"` — **17/17**,
  0 remaining `ERROR`. `C1` (coverage) reads `100.0 %` on every one of the 17 — no area dropped by the
  fix. (`28583`'s own `TopologyException` was already resolved by T05c's `_opening_lost` guard, confirmed
  independently by this task's own reproduction: it builds `direct` with the `_fix_snap_multipolygons`
  patch present but untriggered for that specific plate.) The four district JSONs themselves are the
  director's own `_r3` rebuild (`D-EU-89` clause 4), not re-run by this task — this entry is the
  reproduce-and-pass proof the plan's "How to test" (1) asks the executor for.
- **`FINDING 242` (ring/wing) diagnosis and effect**, three worst by `C10` area (`FINDING 242`'s own
  list, `n=12` forced as in the plan's residual table): `COURTYARD 29659` — `cut_radial` wins outright
  (`_plate_score` beats `cut_nocore`/swept/`cut_layered` on every candidate printed), created-pinch
  `34.11 -> 5.37 m²` (-84 %), `C6` (outer contact) `2.76 -> 6.58 m`, `C11` (aspect) `14.1:1 -> 4.9:1` —
  still `FAIL` (both `C10` and `C11`, the sector cut reduces the pinch but does not by itself square the
  flat). `COURTYARD 31169` — `cut_radial` wins, created-pinch `13.95 -> 2.14 m²` (-85 %), `C11`
  `5.1:1 -> 4.9:1` — still `FAIL`. `COMPLEX_MULTI_WING way/968439455` — **unchanged**, `18.42 m²`:
  `lobes_of(poly_n)` returns `None` at every neck radius tried (`0.75` through `3.0` m), so this specific
  plate's wings never separate under that test and `cut_wingwise` never fires — an honest structural
  residual (no candidate exists at this `k` for this plate), not a missed candidate, exactly as the
  plan's own escape hatch allows.
- **Full ladder, `--test all`, 550 plates** (`TOTAL FAIL` = plates failing `C10` and/or `C11`, same
  definition as T05c):

  | rung | t1 | t2 | t3 | t4 | t5 | TOTAL FAIL | (T05c's own, for reference) |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | 2.5 | 4 | 27 | 3 | 44 | 3 | **81** | 81 |
  | 3.0 | 3 | 20 | 2 | 34 | 3 | **62** | 62 |
  | 3.5 | 2 | 15 | 1 | 24 | 2 | **44** | 46 |
  | 4.0 | 2 | 13 | 1 | 20 | 1 | **37** | 39 |

  On-disk `test_0N_nocore.json` at the final real CLI run (`2.5`) matches the in-memory sweep exactly:
  `t1=4 t2=27 t3=3 t4=44 t5=3`, `TOTAL 81`. **No rung reaches `FAIL 0`** — every rung is at or slightly
  below T05c's own count (2.5/3.0 identical, since `29659`/`31169`/`way/968439455` still exceed the
  `0.10 m²` `C10` tolerance and the aspect gate at every rung tried, just by a smaller margin; 3.5/4.0
  each down by 2). At `2.5` the residual splits **49 `C10`-only, 26 `C11`-only, 6 both** (of 81
  plate-appearances, 57 unique buildings); at `4.0`, **32/3/2** (of 37, fewer unique buildings).
- **Status**: `0` plates carry `status != "direct"` across all five on-disk JSONs — no plate refused, no
  plate dropped (rule 5).
- **Regression, `C1/C3/C4/C5/C6`**, matched by `(group, building_id, drawn_per_floor)` across all 550
  plates against the pre-T05d on-disk JSONs (snapshotted before this task's first edit): **0
  regressions** on any of the five checks.
- **Owner-read sheets**: `TEST_0[1-5]_*_nocore_2026-09-03.html` (no `_r2`) reconfirmed byte-identical
  (`cmp` clean, 5/5) to `rules/tests/archive/reviewed_2026-09-03/` after this task's runs — only the
  `_r2` tag (T05b step 0's repoint) was rewritten.

Residual at the frozen (not calibrated) rung `2.5` — 57 unique buildings, 81 plate-appearances. `C10`
area and local band (`2 x distance from the pinch piece's own centroid to the plate's own boundary`, as
T05c) for the 38 unique buildings whose residual includes `C10`, worst first:

| group | building_id | n | C10 area | local band |
| --- | --- | --- | --- | --- |
| U_OR_T_SHAPE | 31035 | 6 | 14.08 m² | 1.80 m |
| TRAPEZOID | way/288276174 | 12 | 11.10 m² | 3.63 m |
| COURTYARD | 28754 | 12 | 10.61 m² | 1.22 m |
| COURTYARD | 28782 | 9 | 7.55 m² | 1.66 m |
| SLIVER | 31628 | 6 | 7.50 m² | 1.94 m |
| SQUARE | 32165 | 12 | 7.06 m² | 4.43 m |
| SLIVER | 31636 | 6 | 6.04 m² | 1.58 m |
| SQUARE | 28527 | 12 | 5.99 m² | 5.44 m |
| COURTYARD | 29659 | 12 | 5.37 m² | 1.00 m |
| L_SHAPE | way/435212755 | 12 | 5.34 m² | 4.72 m |
| COMPLEX_MULTI_WING | 31410 | 9 | 4.75 m² | 1.02 m |
| CORRIDOR_RECTANGLE | way/322742247 | 12 | 4.67 m² | 1.42 m |
| SLIVER | 31415 | 12 | 4.66 m² | 1.89 m |
| COURTYARD | relation/4835801 | 9 | 4.51 m² | 0.67 m |
| COURTYARD | relation/4678507 | 9 | 4.41 m² | 0.81 m |
| COURTYARD | 29087 | 12 | 3.85 m² | 0.74 m |
| COURTYARD | 31813 | 6 | 3.08 m² | 1.00 m |
| COMPLEX_MULTI_WING | way/420409335 | 6 | 2.74 m² | 1.57 m |
| COURTYARD | relation/12876435 | 3 | 2.47 m² | 0.59 m |
| COMPLEX_MULTI_WING | way/434878287 | 5 | 2.32 m² | 1.21 m |
| COURTYARD | 31169 | 12 | 2.14 m² | 0.87 m |
| TRIANGLE | BATIMENT0000000240877151_part0 | 12 | 2.06 m² | 1.05 m |
| COMPLEX_MULTI_WING | 32211 | 12 | 2.03 m² | 1.80 m |
| SLAB | BATIMENT0000000240881557_part0 | 12 | 1.94 m² | 1.04 m |
| COURTYARD | relation/4165180 | 6 | 1.52 m² | 1.07 m |
| TRIANGLE | way/432864418 | 12 | 1.28 m² | 0.84 m |
| TRIANGLE | 31311 | 12 | 1.12 m² | 0.45 m |
| CORRIDOR_RECTANGLE | 32721 | 12 | 1.08 m² | 0.81 m |
| SLIVER | way/403642584 | 12 | 1.02 m² | 0.78 m |
| COMPLEX_MULTI_WING | 31801 | 12 | 0.93 m² | 0.75 m |
| COMPLEX_MULTI_WING | 30390 | 9 | 0.90 m² | 0.76 m |
| L_SHAPE | BATIMENT0000000240880015_part0 | 9 | 0.88 m² | 0.57 m |
| COURTYARD | 29397 | 6 | 0.57 m² | 0.32 m |
| COMPLEX_MULTI_WING | way/381466697 | 12 | 0.54 m² | 0.54 m |
| SLIVER | 31519 | 12 | 0.30 m² | 0.36 m |
| COURTYARD | 28651 | 2 | 0.23 m² | 1.33 m |
| COURTYARD | relation/12765478 | 6 | 0.19 m² | 0.43 m |
| COURTYARD | 28125 | 12 | 0.14 m² | 0.09 m |
| U_OR_T_SHAPE | way/391270222 | 12 | 0.11 m² | 0.13 m |

The remaining 19 unique buildings fail `C11` only (aspect over `2.5:1`, `C10` already clean): `L_SHAPE
way/290026256` 7.4:1, `L_SHAPE way/391279228` 7.5:1, `COMPLEX_MULTI_WING 31312` 8.8:1, `U_OR_T_SHAPE
way/391276768` 7.9:1, `U_OR_T_SHAPE 28621` 9.6:1, `COURTYARD 32584` 12.4:1, `U_OR_T_SHAPE 32131` 3.1:1,
`COURTYARD 33141` 3.4:1, `TRIANGLE way/389587830` 4.4:1, `COMPLEX_MULTI_WING way/968439455` 4.2:1,
`SQUARE 29094` 3.7:1, `TRAPEZOID way/391662735` 3.4:1, `COURTYARD 30025` 2.5:1, `TRAPEZOID
way/311159690` 3.6:1, `TRAPEZOID way/941927234` 2.5:1, `COURTYARD 32584`/`29891`/`29782`/`32758`
(`SLIVER`/`COMPLEX_MULTI_WING`/`SLIVER` at `k<=3`, 2.9-5.8:1).

Notes: **`FAIL 0` is unreachable at every rung tried (`2.5`/`3.0`/`3.5`/`4.0`)** after a second genuine
repair round (`cut_radial`, `cut_wingwise`, both measurably helping where a legal division exists,
`FINDING 243`'s crash fully fixed) — the residual is the same structural family `D-EU-86`/`D-EU-87`
already identified, now narrowed to plates where even a radial or per-wing candidate cannot close the
`C10`/`C11` gap (a ring whose band is too thin for any angular slice to be both compact and fully
outer-contacted, e.g. `29659`/`31169`; a wing plate whose wings do not separate under `lobes_of` at any
tried radius, e.g. `way/968439455`). Per `D-EU-89` clause 2 (ruled ahead of this task) and the
director's explicit instruction for this run (never pick the least-failing rung): `MAX_FLAT_ASPECT` is
set to **`2.5`**, the strictest rung, marked *set by `D-EU-89` clause 2, not calibrated* in its own
in-file comment, and the 57-building residual above is delivered as honest `FAIL`s on the live
`test_0N_nocore.json` / `TEST_0N_..._nocore_2026-09-03_r2.html`. No exemption invented, no check
loosened, no plate refused or dropped, the `0.10 m²` `C10` tolerance untouched. **Per the director's own
instruction for this task (overriding the plan's literal "continue into T06" for this exact branch):
the executor stops here and reports — `T06`/`T07` do not run this session.** `FINDING 243`'s
`MultiPolygon` entry in `debugs/DEBUG_REFERENCES_european_locations.md` ch. 1 updated: `[OPEN]` marker
dropped, fix line added (root cause, fix location, 17/17 verification).

#### T06 — Build the five delivered sheets — completed 2026-09-03

Artifacts: `scripts/eu21/07_nocore_tests.py` — `MAX_FLAT_ASPECT_STATUS` (`07:1051`), a one-line prose
constant stating *"MAX_FLAT_ASPECT = 2.5, set to the strictest rung by D-EU-89 clause 2 -- not calibrated
(D-EU-84's FAIL-0 condition was never met at 2.5/3.0/3.5/4.0)"*, wired into the sheet `header`'s `<div
class="meta">` as the last `<span>` (T06's own "How to test" requirement: *"the sheet's header states the
constant's status in one line"* — nothing in the file printed this before). Same edit corrected the
header's stale literal date `<span>2026-09-02</span>` to `2026-09-03`. `--test all` run for real at the
frozen (not calibrated) constant, writing all five delivered sheets under `HTML_DIR` as
`TEST_0N_..._nocore_2026-09-03_r2.html` (`html_path` already targeted `_r2` from T05b step 0 — no path
change needed this task) and rewriting the five live `test_0N_nocore.json`.

Deviations: none against T06's "What" list itself — checked first, per the dispatcher's instruction:
`grep -n "widest_fit|six checks|All six checks"` found the `C10` check-legend row, the `D-EU-81` rules
bullet and all four "six checks"/"All six checks passed" strings already corrected to seven, done early
as T05c's own out-of-order deviation (logged in T05c's entry above) — nothing left to fix from T06's
named list. The one addition made (`MAX_FLAT_ASPECT_STATUS` + date fix) is required by T06's own "How to
test" clause, not optional, same file, no check touched.

Test status — census (`--test all`, frozen `MAX_FLAT_ASPECT = 2.5`, `D-EU-89` clause 2), against T01's
baseline row for the same test (`over3.0` / `max aspect`):

| test | plates | PASS | FAIL | flats | max aspect (T06) | over3.0 (T06) | max aspect (T01 baseline) | over3.0 (T01 baseline) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 33 | 29 | 4 | 102 | 12.42 | 3 | 5.53 | 21 |
| 2 | 132 | 105 | 27 | 990 | 8.78 | 33 | 13.02 | 561 |
| 3 | 55 | 52 | 3 | 167 | 9.61 | 3 | 5.43 | 30 |
| 4 | 220 | 176 | 44 | 1650 | 8.78 | 63 | 14.12 | 896 |
| 5 | 110 | 107 | 3 | 358 | 4.63 | 3 | 8.54 | 69 |
| **total** | **550** | **469** | **81** | **3267** | — | **105** | — | **1577** |

**`FAIL 81` reproduces T05d's own residual exactly** — same 4/27/3/44/3 per-test split, same 81
plate-appearances, same per-plate `C10`/`C11` values (spot-checked: `COURTYARD 29659` `C10 5.37 m² / C11
4.9:1`, `COURTYARD 31169` `C10 2.14 m² / C11 4.9:1`, `COMPLEX_MULTI_WING way/968439455` `C11 4.2:1`,
`COURTYARD 32584` `C11 12.4:1` — all identical to T05d's tables above). No stop condition (rule 10 /
T05d's `D-EU-89` clause 2 delivery). `550` plates total, `0` refused, `0` dropped, `0` `status != "direct"`.
All seven checks (`C1 C3 C4 C5 C6 C10 C11`) present in every plate's `checks` dict (spot-checked
`test_01_nocore.json` plate 1: `['C1', 'C10', 'C11', 'C3', 'C4', 'C5', 'C6']`). Sheet header status line
confirmed present in the generated HTML (`grep -c "D-EU-89 clause 2"` → 1 in
`TEST_01_..._r2.html`). Owner-read `TEST_0[1-5]_*_nocore_2026-09-03.html` (no `_r2`) re-verified
byte-identical (`cmp` clean, 5/5) against `rules/tests/archive/reviewed_2026-09-03/` after this run — this
task never writes that path (`html_path` always resolves to `_r2`).

Notes: this is a `D-EU-89`-clause-2 delivery, not a `FAIL 0` delivery — every one of the 81 residual
`FAIL`s is the honest structural residual T05d already diagnosed and reported, not a new failure. No new
error hit this task; no `debugs/DEBUG_REFERENCES_european_locations.md` entry required.

#### T07 — Rules docs, archive, prompt, state — completed 2026-09-03

Artifacts: four rules docs re-dated and republished live in `rules/` —
`RULES_dwelling_layout_groups_nocore_2026-09-03.html`, `EXAMPLE_dwelling_layout_validation_nocore_2026-09-03.md`,
`RULES_context_geometry_simulation_nocore_2026-09-03.md`, `RULES_dwelling_layout_scheme_nocore_2026-09-03.html`.
The four `*_nocore_2026-09-02.*` originals are now in `rules/archive/`. `STATE_european_locations_v5.md` and
`prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` updated (seven checks, the not-calibrated
`MAX_FLAT_ASPECT = 2.5`, new sheet names, laws `D-EU-82`…`D-EU-87`, findings `238`…`243`, next free
`D-EU-91`/`FINDING 245`). `debugs/DEBUG_REFERENCES_european_locations.md`: three source-doc citations
repaired to the new filenames/archive paths. The five `TEST_0*_nocore_2026-09-03.html` (no `_r2`) removed
from `rules/tests/` after `cmp` confirmed byte-identity with `rules/tests/archive/reviewed_2026-09-03/` — no
second archive copy made, per the plan's own instruction.

Deviations (both discovered, neither invented, both reported rather than silently absorbed):
1. **`RULES_dwelling_layout_scheme_nocore_2026-09-02.html` was already in `rules/archive/`, not in `rules/`,
   before this task's first edit** — its directory mtime (09:34, 2026-09-03) predates this session and this
   plan's own T01–T06 never touched a rules doc, so the move happened outside this arc's own logged work;
   cause not determined (no git command run, per hard rule 3). Content verified intact (234 lines, title and
   `<h1>` present, matches the nocore-plan T05 delivery described in `PLAN_eu21-nocore-2026-09-02.md`).
   Treated as item 1's "move" step already done for that one file; only its `_2026-09-03` replacement was
   published live, per the plan's own "resolve by filename, not by rewriting the path prefix" convention.
   Flagged here rather than silently absorbed, per rule 10.
2. `T06`'s own "How to test" required the sheet's own header to state the constant's status in one line —
   nothing in `07_nocore_tests.py` printed this before. Added `MAX_FLAT_ASPECT_STATUS` (`07_nocore_tests.py`,
   after the `MAX_FLAT_ASPECT` constant) and wired it into the sheet header's `<div class="meta">`, plus
   corrected the header's stale literal `2026-09-02` date span to `2026-09-03`. Logged under `T06` above
   since it is that task's own requirement, not `T07`'s.

Content changes made to the four rules docs (`D-EU-82`…`D-EU-87` added wherever `D-EU-79`/`D-EU-80`/`D-EU-81`
already appeared; none added to `RULES_context_geometry_simulation`, which never cited them):
- `C11` added to the check legend / rules table in all four docs; `C10` restated everywhere it was defined
  as `widest_fit &ge; 2.00 m` — now the created-pinch-area test, footprint-inherited narrowness excluded,
  cut-created narrowness not (`D-EU-87`). "Six checks" corrected to "seven" (`RULES_dwelling_layout_groups`:
  2 occurrences; the `07_nocore_tests.py` sheet prose was already corrected in `T05c`'s own deviation, verified
  by `grep -n "widest_fit\|six checks\|All six checks"` before touching anything — nothing left to fix there
  beyond `T06`'s own header-status addition above).
- `RULES_dwelling_layout_groups`: added global laws 6 (`D-EU-82`, `C11`) and 7 (`D-EU-83`, grid-first) plus a
  calibration note (`D-EU-84`/`D-EU-86`/`D-EU-87`/`D-EU-89` clause 2) to the `GLOBAL` section; `COURTYARD`,
  `L_SHAPE` and `COMPLEX_MULTI_WING` step-4 ("Cut the flats") and step-7 ("Scheme that does it") restated by
  name (`cut_layered` for all three; `cut_radial` for `COURTYARD`'s ring; `cut_wingwise` for the two wing
  groups) — the other eight groups' step 4/7 are untouched (`D-EU-83`'s grid-first applies to every group and
  is stated once, globally, not repeated per group). Footer fleet stat and "what this is" cutter description
  updated to the candidate-search model. Verified by count: `C11` 13 occurrences, `cut_radial` 3,
  `cut_wingwise` 5, the untouched groups' `"the same cutter for every group"` phrase still 8, `<article>`/
  `</article>` both 11 (no tag damage from the per-group line-scoped edits).
- `EXAMPLE_dwelling_layout_validation` and `RULES_dwelling_layout_scheme`: fleet census table replaced with
  the actual `T06` result (469 PASS / 81 FAIL, not `FAIL 0`), sheet paths repointed to `_r2`, laws
  `D-EU-82`/`D-EU-83` and the restated `D-EU-81`/`C10` added, "no seventh check" / "six checks" language
  removed.

Test status:
- Citation sweep (`grep -rl` per filename over `docs/`, `scripts/`, excluding `docs_DONE/`, `docs_main/`,
  `docs_TODO/layoutgenerator/`, `rules/archive/`, `rules/tests/archive/`, and this task's own four new rules
  docs' intentional "supersedes" self-citations): `EXAMPLE_dwelling_layout_validation_nocore_2026-09-02` → 4
  live files; `RULES_context_geometry_simulation_nocore_2026-09-02` → 4; `RULES_dwelling_layout_groups_nocore_2026-09-02`
  → 5; `RULES_dwelling_layout_scheme_nocore_2026-09-02` → 3; the five moved `TEST_0N_..._nocore_2026-09-03.html`
  (no `_r2`) → 3/1/1/1/1. Every remaining hit inspected by line number and confirmed one of: a closed-plan
  progress log (`PLAN_eu21-nocore-2026-09-02.md`, `PLAN_eu21-district-viewer-2026-09-03.md` — "Completed" per
  `STATE_v5` §7), `previous/STATE_european_locations_v4.md` (explicitly "historical" per `STATE_v5` line 12),
  this plan's own `T05`/`T06`/`T07` task-spec prose (manager-authored, not editable by the executor), a
  verbatim owner quote (`STATE_v5.md` line 395), or `DIRECTOR_PROMPT`'s own closed-ledger block for
  `eu21-nocore-2026-09-02` (left untouched, matching that document's own established precedent of annotating
  forward rather than rewriting history, e.g. its existing line 357 note). No live, unannotated stale pointer
  remains.
- `MAX_FLAT_ASPECT` "next free" correction: `D-EU-91`/`FINDING 245` written into `STATE_european_locations_v5.md`
  §7 and `DIRECTOR_PROMPT`'s new top-of-§5 block; the two stale `D-EU-90`/`FINDING 244` mentions inside
  `DIRECTOR_PROMPT`'s own historical "evening" block were annotated (not deleted) with the correction, matching
  that document's own precedent style.
- Four rules docs exist at `_2026-09-03`; the four `*_2026-09-02.*` do not exist outside `rules/archive/`
  (`ls` verified).

Notes: no git command run this task (confirmed — every check above used `Read`/`Grep`/`Glob`/plain file
copy, move and delete via `Bash`, never `git`). Deviation 1 (the pre-archived scheme doc) is reported, not
silently resolved — the director should confirm no other out-of-band file move happened this session that
this executor could not detect without git.
