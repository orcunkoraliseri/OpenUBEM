# PLAN — `eu21-colour-repair` — turn as many red plates green as the ruled cutter allows

**Slug:** `eu21-colour-repair` · **Opened:** 2026-09-03 · **Director:** this session · **Executor:** fresh Sonnet
**Specs (read-only):** `docs/docs_ACTIVE/europeanLocations/STATE_european_locations_v5.md` §4 (rulings `D-EU-79`…`D-EU-90`)
and §3 (findings through `FINDING 244`).
**Diagnoses this plan executes:** `debugs/DEBUG_district_red_buildings_diagnosis_2026-09-03.md` §4 Steps 2 and 3;
`debugs/DEBUG_district_orange_buildings_diagnosis_2026-09-03.md` §4 (**not** executed — see §2).
**Predecessors:** `PLAN_eu21-compactness-2026-09-03.md` (closed, `CP-3`), `PLAN_eu21-district-viewer-2026-09-03.md`
(closed, `T05` = the `_r3` build).

---

## 1. Why this plan exists

The `_r3` district build is accepted (`error = 0` in all four JSONs) but the owner's aim was never a report —
it was to turn the coloured buildings green. Measured on `_r3` (`openubem/outputs/eu_evidence/EU-21/district_plans/*_nocore_2026-09-03_r3.json`,
`summary` blocks):

| colour | meaning | `_r3` count | this plan |
| --- | --- | --- | --- |
| purple | `status = ERROR`, cutter raised | **0** | already solved by `FINDING 243`; nothing to do |
| orange | `status = REFUSED_K_GT_12` | **23** (Madrid 7 · Lyon 3 · London 13 · Bologna 0) | **in scope, T05** — cut attempted at the declared `k`, judged by the same seven checks (`D-EU-92`) |
| red | `verdict = FAIL` on one of the seven checks | **509** | **in scope** |
| green | `PASS` 2,012 (bright) + `GENERIC_NO_CENSUS` 1,642 (dark) | 3,654 | target: grows |

Red by failing check, fleet, `_r3`: `C11` **291** · `C10` **168** · `C5` **74** · `C4` **13** · `C6` **11** ·
`C1` 0 · `C3` 0. (A plate may fail more than one, so these sum above 509.)

**The honest ceiling of this plan.** `C11` (slenderness) is the largest bucket and is the one the red report
proposed to fix with a `k = 1` sliver *exemption*, which §2 forbids. A genuinely slender plate cut into flats
yields slender flats; no search improvement can make a 6 m-wide terrace produce 2.5 : 1 rooms. This plan
therefore targets the buckets that are cut-strategy defects — `C10`, `C5`, `C4`, `C6`, plus whatever share of
`C11` a better cut direction recovers — and **promises no number in advance**. The red report's "≥ 98 % PASS"
claim (its §4 closing line) is its executor's projection, not an acceptance criterion, and is not adopted here.

---

## 2. Hard rules for the executor — non-negotiable

1. 🔴 **No exemption, no named-building list, no per-morphology carve-out, no loosened rung** (`D-EU-84`,
   `D-EU-86`, on the director's measurement in `FINDING 240` that the footprint excuse is false). If a plate
   fails, it fails and is printed as failing.
2. 🔴 **`MAX_FLAT_ASPECT` stays `2.5`** (`07_nocore_tests.py:1049`, `D-EU-89` clause 2). Do not change it, do
   not make it per-group, do not make it depend on `k`.
3. 🔴 **`k` is never clamped, selected, sampled or redistributed across storeys** (`D-EU-88` clause 1: `k` is
   what `load_universe` computes). This bars the orange report's Tier 1 (habitable-area clamp) and Tier 3
   (storey rebalancing), and the red report's Diagnosis 4 (façade-cap redistribution) — all three rewrite `k`.
   T05 does the opposite: it keeps `k` exactly as declared and simply *tries* the cut.
4. 🔴 **Seven checks only** — `C1 C3 C4 C5 C6 C10 C11`. Do **not** add `C12` (red report §4 Step 5);
   that is `FINDING 244`, already recorded, and needs the owner's ruling.
5. 🔴 **`_plate_score` and `_fully_ok` keep their current ordering and thresholds**
   (`07_nocore_tests.py:730` and `:763`). You may add *candidates* to the search; you may not change how
   candidates are judged. Changing the judge is how a regression gets scored as an improvement.
6. 🔴 **Never overwrite a delivered artifact** (`D-EU-85`). The `_r3` JSONs, the `_r3` pages, and everything
   under `plans3D/archive/` are frozen. This plan's build is tagged `2026-09-03_r4` and writes new filenames.
7. 🔴 **No EnergyPlus run of any kind** (`D-EU-55`) — no IDF is simulated by this plan.
8. 🔴 **No git.** No `add`, `commit`, `stash`, `restore`, `checkout`, `reset`, `clean`. The dirty tree is the owner's.
9. **No `.py` under `docs/`.** No new files outside §3's layout. No "helpful extras".
10. If the spec here and a ruling in `STATE_european_locations_v5.md` §4 conflict, **STOP and quote the conflict**.
    Do not resolve it yourself.

---

## 3. File layout

**Edited (feature code):**
- `scripts/eu21/07_nocore_tests.py` — the cutter. All T02–T04 algorithm work lands here.
- `scripts/eu21/08_district_viewer.py` — **T05 only**, and only inside `process_census`'s `k > 12` branch
  (`:165-169`). No other function in this file is touched.

**Written (evidence, new filenames only):**
- `openubem/outputs/eu_evidence/EU-21/rules_tests/colour_repair_bench_<TXX>.json` — the bench output of T01–T04.
- `openubem/outputs/eu_evidence/EU-21/district_plans/<DISTRICT>_nocore_2026-09-03_r4.json` — T05, four files.
- `docs/docs_ACTIVE/europeanLocations/plans3D/archive/PLANS_<DISTRICT>_nocore_2026-09-03_r4.html` — T05, four files (**archived 2026-09-03** on the owner's sentence *"archive r3, r4"*; superseded by `_r5`, T07).

**Appended:** §8 of this document, one entry per task.

**Read-only, never edited:** `STATE_european_locations_v5.md`, the three `debugs/DEBUG_district_*_2026-09-03.md`
reports, everything under `rules/`, everything under `plans3D/archive/` and `plans3D/previous/`,
every `*_r3.*` and `*_r2.*` artifact, `openubem/geometry/european_residential.py` (import from it, never copy
or edit), and every part of `08_district_viewer.py` outside the `k > 12` branch named above.

---

## 4. Dependency decisions — pinned

4.1 **The cutter is `scripts/eu21/07_nocore_tests.py` and nothing else.** `08_district_viewer.py:37` loads it as
a module (`M07`) and calls `M07.build_flats(p, k)` at `:211`. Improving `build_flats` improves the district
build with no viewer change. Do not fork the cutter, do not copy functions into the viewer.

4.2 **Reflex-vertex geometry is imported, never re-implemented.**
`openubem/geometry/european_residential.py` already exports `_reflex_vertex_count` and `_split_at_reflex_vertex`
(both imported by `scripts/eu20_morphology_atlas.py:30` and `scripts/eu17_refusal_census.py:61-62`). Import them.

4.3 **Frame helpers stay where they are.** `_normalize` (`05_group_cutters.py:76`), `frame` (`:84`),
`to_local` (`:98`), `lobes_of` (bound at `07_nocore_tests.py:82`). Import, do not re-derive.

4.4 **Shapely only.** No new third-party dependency. No `scipy`, no `networkx`, no medial-axis library —
if a medial axis is needed, approximate it with what Shapely already offers or drop that candidate.

4.5 **Determinism.** The cutter must stay deterministic: same input → byte-identical flats. No RNG, no
wall-clock, no set iteration order leaking into geometry. `cutter_sha256` is printed into every JSON and page
footer and is how the owner tells builds apart.

---

## 5. Facts with citations — read these before writing code

5.1 **`build_flats` (`07_nocore_tests.py:864`) is a candidate search, not a single algorithm.** For
`rows_` in `1..min(k, MAX_GRID_ROWS=6)` (`:861`, `:890-891`) and `theta_offset` in `(0.0, 90.0)` (`:892`) it
builds candidates, scores each with `_plate_score`, and keeps the best (`:948`). For `rows_ == 1` it also tries
the swept-boundary variant (`_sweep_boundaries`, `:686`, called `:903`), the depth-layered variant
(`cut_layered`, `:472`, called `:911`), the radial-sector variant for a ring (`cut_radial`, `:594`, called
`:920`) and the per-wing variant (`cut_wingwise`, `:626`, called `:929`). Every candidate passes through
`_delobe_and_donate` (`:284`) and `donate_leftovers` (`:245`). If the winner is not `_fully_ok`, a last-resort
`_donate_the_neck` (`:775`) is tried and kept only if it scores better (`:949-955`).

5.2 **This is why adding candidates is the ruled way to improve the result.** The search keeps the best by a
fixed judge. A new candidate can only raise the winning score or be discarded — it cannot regress a plate that
already passes, provided rule 5 of §2 holds. That property is what makes T02–T04 safe, and T05's
no-regression gate is what proves it held.

5.3 **The angle search is the narrowest part of the search.** `theta` comes from `frame(poly_n)`
(`:888`) — the minimum-rotated-rectangle axis — and only `0.0` and `90.0` are added. For a courtyard ring, an
L/T/U-wing, or an angled terrace row, the cut direction that yields compact flats is frequently neither. This
is the same defect the red report describes as "snap cut planes to interior reflex vertices" (§4 Step 3),
stated in the search's own terms.

5.4 **`C10` is the created-pinch opening test** (`D-EU-87`): `pinch_area` (`:1133`), driven by `_pinch_geom`
(`:1108`) and `_opening_lost` (`:1075`); the `_fully_ok` allowance is total pinch ≤ 0.10 m², the measured
float-noise floor (`:763-772`), **never** a widened allowance.

5.5 **`C5` is the simple-outline test**: no interior rings, no flat containing another's representative point,
≤ 40 exterior points (`_plate_score`, `:748-752`). The red report's "donut" failures are flats that inherited
the plate's courtyard ring.

5.6 **`C11` is `flat_aspect(f) <= MAX_FLAT_ASPECT`** (`:1057`, `:1049`), and `C6` is ≥ 2.50 m of contact
between the flat and the plate's outer boundary (`:753-755`).

5.7 **The `_r3` baseline you must reproduce before changing anything** (from the four `*_r3.json` `summary`
blocks): drawn 2,521 / 2,544 (99.1 %); PASS 2,012 (79.1 %); FAIL 509; refused 23; error 0; generic 1,642.
Per district PASS/FAIL: Madrid 803/151 · Lyon 247/47 · London 50/19 · Bologna 912/292.
`cutter_sha256 = 76a124bfda431b38a29bed50a12e3b450d3c9566688d11fbf7422d50b220a844`, `max_flat_aspect = 2.5`.

---

## 6. Task list

### T01 — Bench harness over the `_r3` failing plates

**What.** A repeatable in-process bench that re-cuts a named set of plates with the current cutter and reports
per-check tallies, so every later task is measured rather than asserted.

**Why.** §2 rule 5 forbids moving the judge; the only honest way to show an improvement is the same judge on
the same plates before and after. Without this, T02–T04 are opinions.

**How.** Add nothing to the cutter. Write the bench as a `main()`-level mode inside
`scripts/eu21/07_nocore_tests.py` (a new `--bench` argument on its existing `argparse`, default off, so the
normal run path is untouched), which: reads the four `*_nocore_2026-09-03_r3.json`; selects every plate with
`verdict == "FAIL"` (509) **plus** a control sample of 200 plates with `verdict == "PASS"` taken in file order
(no RNG, §4.5); re-cuts each from its stored `footprint` and `k` via `build_flats`; re-runs `run_checks`
(`:1140`); and writes `rules_tests/colour_repair_bench_T01.json` with, per district and fleet: `n`,
`pass`, `fail`, `fail_by_check`, and the list of `building_id` that changed verdict.

**How to test.** On the unmodified cutter the bench must reproduce `_r3` exactly: **509 FAIL / 0 PASS** in the
FAIL set, **200 PASS / 0 FAIL** in the control set, and `fail_by_check` equal to
`C11` 291 · `C10` 168 · `C5` 74 · `C4` 13 · `C6` 11 · `C1` 0 · `C3` 0. Any deviation means the bench does not
reconstruct the plate the district build cut — **stop and report, do not proceed to T02.**

---

### T02 — Broaden the angle search in `build_flats`

**What.** Extend the `theta_offset` candidate set (`:892`) beyond `(0.0, 90.0)` with directions derived from
the plate's own geometry.

**Why.** §5.3: the winning cut direction for a wing, ring or angled row is often neither frame axis. This is a
search broadening — the judge is untouched, so by §5.2 no passing plate can regress.

**How.** Build the candidate angle set per plate, in this order and deduplicated to 1.0° resolution:
(a) `0.0` and `90.0` (today's two, always first so ties keep today's answer);
(b) the direction of every exterior edge at least 15 % of the plate's perimeter, normalised into `[0, 90)`;
(c) the bisector direction at each reflex vertex found by `_reflex_vertex_count`'s own denoise path (§4.2).
Cap the set at **12 angles per plate** — take (a), then (b) longest-edge-first, then (c) — so the search cost
stays bounded. Apply the same set to both the `rows_ == 1` branch and the `cut_grid` branch. Nothing else changes.

**How to test.** Re-run the T01 bench → `colour_repair_bench_T02.json`. Required: **control set stays
200 PASS / 0 FAIL** (no regression), and total FAIL in the failing set strictly decreases. Report the
`fail_by_check` delta per check. Also report the wall-time multiplier vs T01 — if the bench is more than
**4×** slower, reduce the cap from 12 and re-measure rather than shipping a build that cannot finish.

---

### T03 — Reflex-vertex boundary snapping

**What.** After a candidate's cut boundaries are chosen, snap each boundary that passes within
**0.75 m** of an interior reflex vertex onto that vertex.

**Why.** The red report's §4 Step 3, and the direct cause of most `C10` created-pinch failures: a cut that
misses a re-entrant corner by a few decimetres leaves a neck that the opening test then measures.

**How.** Operate inside the `rows_ == 1` swept-boundary path (`_sweep_boundaries`, `:686`) and the `cut_grid`
column boundaries: given boundary positions in the local frame, project each candidate reflex vertex into the
same frame and move a boundary to it when the gap is ≤ 0.75 m and the move does not reorder boundaries or
produce a zero-width column. Use `_split_at_reflex_vertex` / `_reflex_vertex_count` by import (§4.2). Snapping
produces one additional candidate; it never replaces the unsnapped one.

**How to test.** Bench → `colour_repair_bench_T03.json`. Required: control set 200 PASS / 0 FAIL; `C10`
failures strictly below T02's; no check's failure count above T02's.

---

### T04 — Courtyard ring bisection at low `k`

**What.** A new candidate for ring-shaped plates (`poly.interiors` non-empty) with `k <= 2`: bisect the ring
across its narrowest bridge into C-shaped flats instead of leaving a flat that inherits the hole.

**Why.** The red report's §4 Step 2, and the direct cause of the `C5` bucket: at `k = 1` the single flat *is*
the ring, so it carries an interior ring and fails the simple-outline test by construction. `cut_radial`
(`:594`) already handles rings but needs enough sectors to be worth choosing.

**How.** Extend `cut_radial` (or add a sibling next to it, called from the same place, `:920`) so that for
`k == 1` it returns the ring cut once across its narrowest bridge and re-merged into a single simply-connected
flat where that is possible, and for `k == 2` it returns two C-flats split at the two narrowest bridges.
Return `None` on a non-ring plate exactly as today. `_plate_score` decides whether the result wins.

**How to test.** Bench → `colour_repair_bench_T04.json`. Required: control set 200 PASS / 0 FAIL; `C5`
failures strictly below T03's; no check's failure count above T03's. Report how many of the 74 `C5` plates
are rings with `k <= 2` versus other causes — a residual is expected and must be named, not hidden.

---

### T05 — Orange: attempt the cut at the declared `k`, and let the seven checks judge it

**What.** Replace the unconditional `k > 12` refusal with an *attempt*: cut the plate at its declared `k`, run
the same seven checks, and keep the refusal only for plates that do not pass them.

**Why.** Owner's sentence, 2026-09-03: *"about orange continue as you progress … to solve as much as orange
buildings, lets go"*, recorded as `D-EU-92`. The refusal at `08_district_viewer.py:165-169` fires **before the
cutter is ever called**, so no evidence has ever existed that these 23 plates cannot be cut — `D-EU-65` was a
declared ceiling, never a measurement. This task produces that measurement.

🔴 **This is not an exemption and must not become one.** `k` is still exactly what `load_universe` computed
(§2 rule 3) — nothing is clamped, sampled or redistributed. The plates are subjected to the *same* seven
checks as every other plate, at the *same* thresholds. A plate turns green only by passing them. If it fails,
it is red or refused, and it is printed that way.

**How.** In `08_district_viewer.py`, `process_census`: keep the `k > 12` branch, but before refusing, run
`build_plate` exactly as the `k <= 12` path does (`:170-172`). If the resulting plate's `verdict` is `PASS`,
keep the plate as `status = "direct"` and record `"k_gt_12_attempted": True` on the record. Otherwise keep
`status = "REFUSED_K_GT_12"` with its existing message, and add `"k_gt_12_attempted": True` plus the
`fail_by_check` of the attempt so the residual is inspectable. Guard the attempt with `try/except` and a
per-plate time budget of **120 s**; on exception or timeout, refuse as today and record the reason — a plate
that hangs the build is a refusal, never a crash (`D-EU-89` clause 3: `error` must stay 0).

**How to test.** Run the attempt over the 23 orange plates only (reuse the T01 bench harness, feeding the
`REFUSED_K_GT_12` records from the `_r3` JSONs) → `colour_repair_bench_T05.json`. Report, per district and
fleet: how many of the 23 pass all seven, how many fail and on which checks, how many raise or time out, and
the wall time of the slowest plate. **No plate may be individually named as an exception in code** (`D-EU-86`).

---

### T05b — Measure the `C11` residual: is the aspect forced by the footprint, or by the cut?

**What.** A measurement, not a fix. For every plate still failing `C11` after T04 (263 fleet-wide: Madrid 61,
Lyon 22, London 7, Bologna 173), decide whether *any* partition into its declared `k` flats could satisfy
`flat_aspect ≤ 2.5`, or whether the footprint forbids it at that `k`.

**Why.** `C11` is now 75 % of the remaining failure mass and the owner's 95 % gate cannot be read honestly
without knowing which half of it is a cutter deficiency and which half is arithmetic. §1 of this plan promises
no number in advance; this task is how that promise is kept. Standing method rule: diagnose before remediating
— no fix belongs in this task.

🔴 **`MAX_FLAT_ASPECT` stays 2.5 and `k` stays exactly what `load_universe` computed** (§2 rules 2 and 3).
This task changes no threshold and no code path used by a build. It writes one evidence JSON and nothing else.

**How.** Add a `--bench C11DIAG` mode alongside the existing bench (same selection path, same file order, no
RNG). For each plate: record `building_id`, district, `k`, plate area `A`, achieved `max_aspect` after T04,
the plate's bounding-box aspect, and a width probe `w` = twice the radius of the largest inscribed circle
(negative-buffer bisection to 0.01 m, Shapely only). Then classify each plate with the strip bound: a flat of
aspect ≤ 2.5 and width ≤ `w` has area ≤ `2.5·w²`, so if `A / k > 2.5·w²` no partition at that `k` can satisfy
`C11` and the plate is **forced**. Otherwise it is **not forced** — the bound does not prove a cut exists, only
that this argument does not forbid one; say exactly that in the output, never "fixable".

**How to test.** `colour_repair_bench_C11DIAG.json` with the per-plate rows and, per district and fleet, the
counts of forced vs not-forced. No plate is modified, no district is rebuilt, no verdict changes. Report the
two counts per district and the fleet total at the checkpoint.

---

### T06 — Rebuild the four districts as `_r4`

**What.** Re-run `scripts/eu21/08_district_viewer.py` for all four districts at tag `2026-09-03_r4`, with
`--generic-no-census`, writing new JSONs and new pages.

**Why.** The bench measures plates in isolation; the district build is the acceptance artifact and the thing
the owner opens.

**How.** For each of `ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`, `IT-BOL-GALVANI2`:
`python scripts/eu21/08_district_viewer.py --district <D> --tag 2026-09-03_r4 --generic-no-census`.
Do **not** pass `--overwrite`. Do not touch `plans3D/index.html` — repointing it is the owner's call
(`D-EU-85`), and this plan does not make it.

**How to test.** Acceptance, all four:
- `error = 0` in every JSON (`D-EU-89` clause 3) — **this is the pass/fail line for the plan**;
- `cutter_sha256` identical across all four and equal to the sha256 of the edited
  `scripts/eu21/07_nocore_tests.py` on disk; `max_flat_aspect = 2.5`; `tag = 2026-09-03_r4`;
- drawn ≥ `_r3`'s 2,521; PASS strictly > `_r3`'s 2,012; refused ≤ 23 (a refusal may only disappear by the
  plate passing all seven checks under T05 — never by a threshold move);
- 🔴 **no-regression gate:** every `building_id` with `verdict == "PASS"` in `_r3` still reads `PASS` in `_r4`.
  Report the count of any that do not, with their ids, and treat a non-empty list as a **failure to report at
  the checkpoint**, not something to fix by tuning;
- page gates on all four `_r4` pages: `grep -c "Dwelling Index"` = 1, `grep -c "srcdoc"` = 0,
  `grep -c -i "kwh\|eui\|energy\|archetype"` = 0, footer shows `2026-09-03_r4`.

---

### T07 — `D-EU-93`: `C11` does not apply to an undivided plate, and rebuild as `_r5`

**What.** Two edits in `scripts/eu21/07_nocore_tests.py`, then a four-district rebuild at tag `2026-09-03_r5`.

**Why.** The owner ruled on 2026-09-03, in their own words *"yes lets go, i say yes D-EU-93"*: at `k = 1` the
single flat **is** the plate, so `C11` measures the footprint the cutter was handed, not the cut it made. No
cut can change that aspect, so the check has nothing to judge. This is `D-EU-93`. It waives `C11` **only** for
an undivided plate; `MAX_FLAT_ASPECT` stays at `2.5` and every other check stays exactly as it is.

**How.**
1. `run_checks` (`:1643-1644`): when `len(live) <= 1`, `checks["C11"]["pass"]` is `True` and `show` reads
   `f"{max_aspect:.1f} : 1 (k=1, D-EU-93)"`. Compute `max_aspect` exactly as now — it is still reported, only
   no longer judged.
2. `_plate_score` (`:968-969`): `c11_ok = (len(live) <= 1) or (max_aspect <= MAX_FLAT_ASPECT)`. Leave the
   `-max_aspect` tie-break untouched. `_fully_ok` reads `c11_ok` from `_plate_score`, so it follows.
3. Update the `C11` row of `build_checks_html` (`:1809-1812`) to state the `k = 1` exemption, and extend
   `MAX_FLAT_ASPECT_STATUS` (`:1514`) with `D-EU-93`.

🔴 Do **not** touch `MAX_FLAT_ASPECT`, any other check, any other threshold, or any file other than
`scripts/eu21/07_nocore_tests.py`. Do not edit `08_district_viewer.py`. Do not touch `plans3D/index.html`.

**How to test.**
- Bench control first: `python scripts/eu21/07_nocore_tests.py --bench D_EU_93` → the 200-plate control set
  must read **200/200**, i.e. no plate that passed before fails now.
- Then, for each of `ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`, `IT-BOL-GALVANI2`:
  `python scripts/eu21/08_district_viewer.py --district <D> --tag 2026-09-03_r5 --generic-no-census`.
  No `--overwrite`. Run them one at a time in the background and read the output JSON; do not sleep-poll.
- Acceptance: `error = 0` ×4; `max_flat_aspect = 2.5`; `tag = 2026-09-03_r5`; `cutter_sha256` identical across
  the four and equal to the sha256 of the edited cutter on disk; drawn ≥ `_r4`'s 2,529; refused = `_r4`'s 15.
- 🔴 **No-regression gate:** every `building_id` reading `PASS` in the `_r4` JSON still reads `PASS` in `_r5`.
  Report any that do not, with ids. A non-empty list is reported, never tuned away.
- 🔴 **Expected, and to be checked against, not steered toward:** +175 PASS fleet-wide (Madrid +49, Lyon +17,
  London +6, Bologna +103), giving Madrid 916/961 = 95.3 %. If the build disagrees with that projection,
  **report the difference** — do not change code to reach it.
- Page gates on all four `_r5` pages: `grep -c "Dwelling Index"` = 1, `grep -c "srcdoc"` = 0,
  `grep -c -i "kwh\|eui\|energy\|archetype"` = 0, footer shows `2026-09-03_r5`.

---

## 7. Stop-and-report points

- **CP-1 — after T01.** Report whether the bench reproduces `_r3` exactly. If not, stop; the bench is wrong
  and every later number would be wrong with it.
- **CP-2 — after T04.** Report the full bench ladder T01 → T02 → T03 → T04: FAIL count and `fail_by_check`
  at each rung, control set at each rung, wall-time multiplier. Then continue into T05.
- **CP-2b — after T05 and T05b, before T06.** Report the orange outcome (how many of the 23 pass all seven,
  how many fail and on which checks, how many raise or time out) and the `C11` forced / not-forced split per
  district. Stop there and wait: the director decides on that evidence whether T06 rebuilds now or whether a
  further cutter task comes first. Do not start T06 until told.
- **CP-3 — after T06.** Report the four-district table, the acceptance list above, the no-regression gate, and
  the T05 orange outcome.
- **CP-4 — after T07.** Report the four-district `_r5` table (drawn / PASS / PASS % / `fail_by_check` / error /
  refused), the no-regression gate against `_r4`, the measured PASS delta per district against the +175
  projection, and the four page gates. Then stop. The simulation decision is the director's, never the
  executor's — **never start an EnergyPlus run** (`D-EU-55`).

At every checkpoint: append the §8 entries for the completed tasks first, then report. State residuals plainly —
a check that does not improve is a result, not a failure of the task.

## 7.1 What happens after CP-3 — do not act on this yourself

The owner's aim is **95 % of a neighbourhood's census plates passing all seven checks**, at which point a
simulation campaign starts (owner's sentence of 2026-09-03, recorded as `D-EU-91`). `_r3` reads Madrid 83.6 % ·
Lyon 83.2 % · London 61.0 % · Bologna 75.7 %, so the gate is open, not met. **The 95 % is read on PASS, never
on drawn** — drawn is already 99.1 % fleet-wide and is not the thing being gated. The executor's job ends at
CP-3: report the numbers and stop. **Never start an EnergyPlus run** (`D-EU-55`); the director evaluates the
gate against `D-EU-91` and the checklist.

---

## 8. Progress log

*(executor appends one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD`, then
**Artifacts** / **Deviations** / **Test status** / **Notes**.)*

#### T01 — Bench harness over the `_r3` failing plates — completed 2026-09-03

**Artifacts:** `--bench` mode added to `scripts/eu21/07_nocore_tests.py` (argparse: `main()` around
`:1569` prior to this plan, now earlier — see T02 note; `run_bench`/`_bench_recut`/`_bench_select`/
`_bench_run_set` added before `main()`). Output:
`openubem/outputs/eu_evidence/EU-21/rules_tests/colour_repair_bench_T01.json`.

**Deviations:** `--test` changed from `required=True` to optional so `--bench` can run without it
(`ap.error` now enforces "one of the two required" manually). No other argparse behaviour changed.

**Test status:** PASS. Bench reproduced the `_r3` baseline exactly: fail-set 509/509 FAIL, 0 PASS;
control-set 200/200 PASS, 0 FAIL; `fail_by_check` C11 291, C10 168, C5 74, C4 13, C6 11, C1 0, C3 0 —
byte-for-byte the numbers in §5.7. Wall time 151.843 s. CP-1 condition met; proceeded to T02.

**Notes:** Selection is the 509 `_r3` FAIL plates (all districts, `status == "direct"`) plus the first
200 `_r3` PASS plates in sorted-glob file order (`ES-MAD-BERRUGUETE, FR-LYO-HAUTCOEURPENTES,
GB-LDN-STDUNSTANS, IT-BOL-GALVANI2`) — no RNG, per §4.5. All 200 control plates came from Madrid
because it alone has 803 PASS plates ahead of the other three districts in that fixed order; this is
a property of the deterministic selection rule, not a defect.

#### T02 — Broaden the angle search in `build_flats` — completed 2026-09-03

**Artifacts:** `scripts/eu21/07_nocore_tests.py`: `_theta_offset_candidates` + `_edge_theta_offsets` +
`_reflex_theta_offsets` + `_bisector_deg` + `_fold_theta_offset` (candidate-angle helpers, ~`:876-982`
in the file as edited); `build_flats`'s `for theta_offset in (0.0, 90.0):` replaced with
`for theta_offset in theta_offsets:` where `theta_offsets = _theta_offset_candidates(poly_n, theta)`
(~`:1178`); import of `_reflex_vertex_count`, `_reflex_vertices`, `_split_at_reflex_vertex` from
`openubem.geometry.european_residential` added near the top of the file (after the `_M05` imports).
Output: `openubem/outputs/eu_evidence/EU-21/rules_tests/colour_repair_bench_T02.json`.

**Deviations (both load-bearing, read before auditing):**
1. §4.2 pins `_reflex_vertex_count` and `_split_at_reflex_vertex` by name; `_reflex_vertex_count`
   returns only a count, not vertex positions, so the bisector direction (T02c) and the T03 snap
   target both need `_reflex_vertices` (plural, positions) — the same module's own point-returning
   helper, run at the identical denoise/detect tolerance. Imported alongside the two pinned names
   rather than re-deriving vertex positions by hand, which §4.2 forbids more directly.
2. **Per-candidate exception safety + per-candidate neck-donation rescue, both required for T02's own
   no-regression test to pass — neither is optional.** Discovered empirically: with only "add angles"
   applied, the control set regressed to 199-198/200. Two independent causes, both fixed:
   (a) a non-cardinal `theta_offset` can hit a GEOS `TopologyException` inside `_delobe_and_donate`
   (`lobes_of`) that the old 0°/90°-only search never exercised — each of the 6 candidate-evaluation
   blocks in `build_flats`'s loop is now wrapped in its own `try/except Exception: pass`, so one
   candidate's crash is discarded (§5.2's "or be discarded"), never fatal to the plate.
   (b) `_donate_the_neck` (the created-pinch rescue) was applied once, only to the loop's final
   winner. A broader search can promote a new raw-best candidate whose own pinch rescue then fails
   (`way/311159688`: old winner raw pinch 6.10 m² rescued to 0.03 m² PASS; new winner raw pinch
   0.12 m² — better raw, but its own rescue attempt found no improvement, so it stayed FAIL). Fixed
   by moving the rescue into a new `_finish_candidate(p, flats, stuck)` helper (`:~1016`) applied to
   **every** candidate before its score is compared, not only the eventual winner; the single
   post-loop rescue block is removed since every stored `best` is already rescued. `_plate_score` and
   `_fully_ok` themselves are byte-identical to before this plan (§2 rule 5) — only *when*
   `_donate_the_neck` fires changed.

**Test status:** PASS. Control set 200/200 PASS, 0 FAIL, `changed_verdict` empty (no regression).
Fail-set FAIL count strictly decreased: 509 → 379 (130 newly PASS). `fail_by_check` T01→T02: C11
291→263, C10 168→60, C5 74→72, C6 11→10, C4 13→13 (unchanged), C1/C3 0/0. Wall time 574.234 s vs T01's
151.843 s = **3.78×** — under the plan's 4× guard rail, so `MAX_THETA_OFFSETS` (12) was not reduced.

**Notes:** Angle candidates: (a) `0.0`/`90.0` literal, unfolded; (b) exterior-edge bearings ≥15% of
perimeter, folded to a `theta_offset` delta via `(bearing - theta) % 180`, folded again into `[0,90)`,
longest-edge-first; (c) reflex-vertex bisector directions at the same fold, from `_reflex_vertices`
denoised at 0.5 m (`european_residential.py:459`'s own tolerance ahead of its own
`_reflex_vertex_count` call — read as "`_reflex_vertex_count`'s own denoise path" per the plan's `T02c`
wording). Deduplicated at 1° resolution, capped at 12, applied identically to the `rows_==1` branch and
the `cut_grid` branch.

#### T03 — Reflex-vertex boundary snapping — completed 2026-09-03

**Artifacts:** `scripts/eu21/07_nocore_tests.py`: `_reflex_points_world`, `_reflex_local_xs`,
`_snap_boundaries` (constants `REFLEX_SNAP_TOLERANCE_M = 0.75`,
`REFLEX_SNAP_DENOISE_TOLERANCE_M = 0.15`, matching `_split_at_reflex_vertex`'s own default); new sibling
functions `_grid_seeds_snapped` (next to `_grid_seeds`) and `cut_grid_snapped` (next to `cut_grid`) —
neither existing function edited. `build_flats` gained two new candidate blocks: a snapped variant of
the `rows_==1` swept-boundary cut, and a snapped variant of the `cut_grid` cut per `rows_`; both are
skipped (no extra cut attempted) when `_snap_boundaries` finds nothing within 0.75 m to move. `Point`
added to the `shapely.geometry` import. Output:
`openubem/outputs/eu_evidence/EU-21/rules_tests/colour_repair_bench_T03.json`.

**Deviations:** none beyond T02's (this task adds candidates only, reusing `_finish_candidate` for
scoring/rescue — no new exception-safety or rescue-timing issue found).

**Test status:** PASS. Control set 200/200 PASS, 0 FAIL, `changed_verdict` empty (no regression). C10
failures strictly below T02's: 60 → 54. No check's failure count above T02's: C4 13/13, C5 72/72, C6
10/10, C11 263/263, C1 0/0, C3 0/0 (all tied or improved; only C10 moved). Fail-set FAIL 379 → 373 (6
more newly PASS). Wall time 809.292 s vs T01's 151.843 s = **5.33×** — above the 4× figure T02's own
guard rail names, but T03's own "how to test" (§6) states no wall-time cap, only T02's does; flagged
here for the director rather than acted on unilaterally (no cap reduction was authorized for T03).

**Notes:** Snapping is additive only — `_grid_seeds`/`cut_grid`/`_sweep_boundaries`'s own unsnapped
candidates are untouched and still evaluated every time; the snapped variant only ever adds a 7th/9th
candidate slot when a boundary is genuinely within 0.75 m of a reflex vertex.

#### T04 — Courtyard ring bisection at low `k` — completed 2026-09-03

**Artifacts:** `scripts/eu21/07_nocore_tests.py`: `RING_BRIDGE_WIDTH_M`/`RING_BRIDGE_MIN_SEPARATION_FRACTION`
constants and `_ring_bridge_candidates` (`:720-745`), `_bridge_cut_rect` (`:747-764`), `cut_ring_bisect`
(`:767-829`) — a sibling next to `cut_radial`, which is not edited. `build_flats` computes
`ring_bisect = cut_ring_bisect(poly, k)` once per plate, guarded to ring plates with `k in (1, 2)`
(`:1301-1306`), and scores it once via `_finish_candidate` after the main search loop (`:1408-1415`).
Output: `openubem/outputs/eu_evidence/EU-21/rules_tests/colour_repair_bench_T04.json`.

**Deviations:**
1. Computed once per plate, not once per `theta_offset` iteration inside the loop, unlike every other
   candidate — the bridge location comes from the ring's own boundary geometry, not from a rotated
   frame, so re-evaluating it per `theta_offset` (up to 12×) would be pure waste. Scored once via the
   same `_finish_candidate`/`_plate_score` path as everything else; the plan's own §5.2 no-regression
   property is unaffected by when a candidate is evaluated, only by how it is judged.
2. **Reference-`poly` bug, found and fixed before the bench ran (not shipped broken).** The `k == 1`
   candidate was first scored against the uncut `poly_n` (to measure C1/C6 against the "real" footprint).
   `_finish_candidate` → `donate_leftovers` (D-EU-80) then found the removed 0.05 m bridge sliver as a
   "leftover" belonging to nobody and re-donated it straight back into the single flat, silently
   undoing the cut (`relation/4154504`: verdict stayed FAIL, `C5 show "9"` unchanged, and a direct check
   showed `interiors == 1` again after `_finish_candidate`). Fixed by scoring the `k == 1` flat against
   its own cut outline (`return cut, [cut], []`, not `poly_n`) — exactly what every other `k == 1`
   candidate already does (one flat, one plate, identical boundary), not a new pattern.
3. **This candidate removes real plate area** — a `RING_BRIDGE_WIDTH_M = 0.05` m rectangle cut through
   the ring's own wall at its narrowest bridge, the mechanism by which a closed ring becomes an open
   C-flat. Measured evidence this did not cost coverage: `C1` stayed **0** in both the T04 fail set and
   the control set (`fail_by_check` `C1: 0`, same as every rung since T01), and the control set stayed
   **200/200 PASS** with `changed_verdict` empty — no plate anywhere in the bench lost coverage over the
   0.999 floor because of the 0.05 m cut.
4. The `k == 2` path is implemented and geometrically validated (batch-tested to produce two valid,
   hole-free, ≥99.9%-coverage C-flats whenever a plate has exactly one courtyard), but every one of the
   13 `k == 2` C5-failing plates in the fleet has 3–9 interior rings (multiple courtyards), so
   `cut_ring_bisect` correctly returns `None` for all of them — the bench never exercised the `k == 2`
   success path on real data. Reported plainly, not hidden.

**Test status:** PASS. Control set 200/200 PASS, 0 FAIL, `changed_verdict` empty (no regression). C5
failures strictly below T03's: 72 → 30. No check's failure count above T03's: C4 13/13, C6 10/10, C10
54/54, C11 263/263, C1 0/0, C3 0/0. Fail-set FAIL 373 → 349 (24 more newly PASS — fewer than the 44
plates whose own C5 check now passes, because some of those 44 still fail on C6/C10/C11 independently).
Wall time 830.806 s vs T01's 151.843 s = **5.47×** (T04, like T03, has no wall-time cap in its own how
to test). Fail-set PASS by district: Madrid 64/151, Lyon 16/47, London 9/19, Bologna 71/292. Remaining
FAIL by district and check: Madrid 87 (C4 1, C5 5, C6 2, C10 21, C11 61), Lyon 31 (C4 1, C5 5, C6 1,
C10 3, C11 22), London 10 (C10 3, C11 7), Bologna 221 (C4 11, C5 20, C6 7, C10 27, C11 173).

**Notes — the required residual accounting (§6 T04 how to test).** Baseline 74 C5 fails decompose
exactly as: 44 single-ring plates at `k ≤ 2` (structurally addressable — geometry batch-checked
43/44 valid+≥99.9% coverage before wiring in; the bench's own C5 tally confirms the full 44 now pass
their own C5 check), 26 multi-ring plates (`poly_n.interiors` count 2–9, any `k` — `cut_ring_bisect`
only ever targets the single largest ring and returns `None` when another piece would still inherit a
remaining hole), 4 non-ring C5 fails (donut-unrelated causes: `> 40` exterior points or a contained
representative point, `_plate_score`/`:748-752`), 0 single-ring plates at `k > 2` (none exist in this
set). `44 + 26 + 4 = 74`. Post-T04, `C5` fails fleet-wide = 30 = `26 + 4` exactly — every one of the 44
structurally-addressable plates now clears its own C5 check; the 30 that remain are precisely the ones
this candidate was never designed to reach. Residual named, not hidden: multi-ring plates are a named
limitation, split by `k` — **13 of the 13 `k == 2` C5-failing plates** and **11 of the 55 `k == 1`
C5-failing plates** (multi-ring, `poly_n.interiors` count 2–9) return `None` from `cut_ring_bisect` and
are untouched by this task; the 4 non-ring causes are out of scope by construction.

**CP-2 position.** Cumulative T01→T04: 160 of 509 baseline FAIL plates recovered. `C5` 74 → 30 and
`C10` 168 → 54 across T02–T04; `C11` 291 → 263 is essentially unmoved and is now on **263 of the 349**
still-failing plates — **75 %** of the remaining fail-set, by far the largest single bucket, matching
§1's own honest-ceiling warning that `C11` (slenderness) is the one this plan promised no number in
advance for.

#### T05 — Orange: attempt the cut at the declared `k`, and let the seven checks judge it — completed 2026-09-03

**Artifacts:** `scripts/eu21/07_nocore_tests.py`: `K_GT_12_TIMEOUT_S = 120` and
`attempt_k_gt_12(grp, r, p, k)` (added directly after `build_plate`) — runs
`build_plate("district", grp, r, p, k, "own", k)` inside a `concurrent.futures.ThreadPoolExecutor(max_workers=1)`,
guarded by `fut.result(timeout=120)`; on success returns `(plate, None)` whatever its verdict, on a
timeout or any exception returns `(None, error_str)` and never raises. `08_district_viewer.py`,
`process_census`'s `k > 12` branch only (nothing else in the file touched): calls
`M07.attempt_k_gt_12(grp, r, p, k)`; if it returns a plate with `verdict == "PASS"`, keeps
`status = "direct"` and the plate fields, plus `k_gt_12_attempted: True`; otherwise keeps
`status = "REFUSED_K_GT_12"` with its original message, `k_gt_12_attempted: True`, and either
`k_gt_12_attempt_error` (timeout/exception text) or `fail_by_check` (the list of failing check ids
from the attempt). Bench: `_bench_orange_select`/`_bench_orange_run` (07_nocore_tests.py, reusing
`load_universe`/`usable_polygon`/`centred`/`_M04.cls`/`attempt_k_gt_12` -- no cutter logic
re-derived), selects the 23 `REFUSED_K_GT_12` `_r3` records in sorted-glob file order (§4.5, no RNG),
wired into the existing `run_bench` under `--bench T05`. Output:
`openubem/outputs/eu_evidence/EU-21/rules_tests/colour_repair_bench_T05.json`.

**Deviations:** none from §6 T05's "How". One implementation choice the plan leaves open: the
per-plate `fail_by_check` recorded on a refused attempt is a list of failing check ids (e.g.
`["C10","C11"]`), not a count dict -- the natural per-plate form; the aggregate count-dict shape is
kept for the bench's own district/fleet tallies.

**Test status:** PASS. `--bench T05` (background, wall time 140.622 s, slowest single plate 19.166 s):
fleet `n` 23, `pass` 8, `fail` 15, `raised` 0, `timed_out` 0 (`D-EU-89` clause 3 held -- `error` stays
0). Fleet `fail_by_check`: `C6` 6, `C10` 11, `C11` 6, `C1`/`C3`/`C4`/`C5` all 0. Per district: Madrid
`n` 7, pass 1, fail 6 (`C6` 1, `C10` 5, `C11` 3); Lyon `n` 3, pass 1, fail 2 (`C11` 2); London `n` 13,
pass 6, fail 7 (`C6` 5, `C10` 6, `C11` 1); Bologna `n` 0 (no orange plates in `_r3`). No plate named
as an exception anywhere in code (`D-EU-86`).

**Notes:** `k` was never touched -- each attempt ran `build_flats` at exactly the `_r3`-declared `k`
(17–23 range for these 23 plates), consistent with `attempt_k_gt_12`'s own docstring guarantee. A
pre-existing `RuntimeWarning: divide by zero/invalid value encountered in buffer` (shapely/GEOS,
stderr only) surfaced intermittently during both T05 and T05b's bench runs; traced to `build_flats`'s
own pre-existing candidate search (unrelated to this task's new code -- confirmed by isolating
`_bench_recut`/`attempt_k_gt_12` calls independently), never raised as an exception, and every plate
in both benches completed with a verdict (`raised` 0 in both). Not fixed, not registered in the debug
references file -- nothing was debugged or changed because of it; flagged here for visibility only.

#### T05b — Measure the `C11` residual: is the aspect forced by the footprint, or by the cut? — completed 2026-09-03

**Artifacts:** `scripts/eu21/07_nocore_tests.py`: `_max_inscribed_radius(poly, tol=0.01)` (negative-buffer
bisection to the plan's 0.01 m tolerance, Shapely only -- grows an initial half-bbox-diagonal guess
until infeasible, then bisects); `_c11_strip_metrics(poly, k)` (the strip-bound classifier itself,
shared by every caller, not re-derived per site); `_bench_c11diag_select` (reuses `_bench_select`'s
fail set -- same selection path, same file order, no RNG, §4.5) and `_bench_c11diag_run`, wired into
`run_bench` under `--bench C11DIAG`; `_bench_c11falsify_select`/`_bench_c11falsify_run` (the
coordinator's falsification check, added mid-task -- reuses `_bench_select`'s 200-plate control set),
wired into `run_bench` under `--bench C11FALSIFY`. No threshold, no build path, no verdict touched
(§2 rules 2/3, this task's own §6 header). Outputs: `colour_repair_bench_C11DIAG.json` (263 per-plate
rows) and `colour_repair_bench_C11FALSIFY.json` (200 control-plate rows).

**Deviations:** the strip bound (`A/k > 2.5·w²`) specified in §6 T05b's "How" was implemented exactly
as written, then falsified and withdrawn mid-task on the coordinator's instruction -- see Test status.
It is replaced by an exact argument the coordinator supplied: at `k = 1` there is no partition to
choose (the single flat *is* the plate), so `flat_aspect` is a property of the footprint alone, and
every `k = 1` plate still failing `C11` is forced by definition, exactly, with no bound needed.

**Test status:** measurement only (no plate modified, no district rebuilt, no verdict changed).
`--bench C11DIAG` (background, wall time 708.041 s): selection = all 509 `_r3` baseline FAIL plates,
re-cut with the current (T01–T04-included) cutter; 263 still fail `C11`
(`raised_or_no_longer_failing_C11` = 246 = 509 − 263, 0 of those from a recut exception) -- exactly
reproduces T04's own CP-2 tally of 263.
The strip bound was then **falsified** on `--bench C11FALSIFY` (foreground, wall time 0.166 s):
applied unchanged to the 200-plate control set, every one of which already `PASS`es all seven checks
(so a partition with every flat at aspect ≤ `MAX_FLAT_ASPECT` is known to exist for each). The bound
wrongly called **2 of 200 "forced"**: `way/288447771` (Madrid, k=1, area 41.44 m², w 3.86 m, bound
37.22 m² < area, plate's own aspect 1.17:1 -- a known PASS) and `way/311431849` (Madrid, k=1, area
451.53 m², w 11.75 m, bound 345.37 m² < area, plate's own aspect 1.01:1 -- a known PASS). Both are
counterexamples: a "forced" verdict on a plate already proven passable is a contradiction, so the
bound is unsound (the inscribed-circle width probe underestimates achievable width on non-convex
footprints) and is **withdrawn** -- not repaired, not used in any conclusion below.
In its place, the exact `k = 1` argument (no bound, supplied by the coordinator): of the 263 plates
still failing `C11`, **187 have `k = 1`** and are forced by definition -- Madrid 50, Lyon 17, London 6,
Bologna 114 (verified directly against `colour_repair_bench_C11DIAG.json`'s 263 rows, filtering on
`k == 1`, before this entry was written). The remaining **76 have `k ≥ 2`** and are **unresolved** --
Madrid 11, Lyon 5, London 1, Bologna 59. `187 + 76 = 263`. The 175/88 strip-bound split is **not**
reported as a result anywhere in this document.

**Notes:** "unresolved" is reported exactly as required for the 76 `k ≥ 2` plates -- no partition was
shown to exist or not exist for them, and none is called "fixable". The 187 `k = 1` plates need no
such qualifier: `flat_aspect(plate) > 2.5` at `k = 1` is a direct measurement of the footprint the
cutter was given, not an artifact of the search.

**CP-2b position.** Orange (T05): 8 of 23 turn green by attempting the cut at declared `k` under the
same seven checks; 15 remain refused, dominated by `C10` (11) and `C6` (6), with `C11` at 6; 0 raised,
0 timed out -- the ceiling is measured, not assumed, and no plate was exempted to get there.
`C11` residual (T05b, strip bound withdrawn, `k = 1` argument only): of the 263 plates still failing
`C11` after T04, **187 are forced by definition** (`k = 1`, no partition exists to try) -- Madrid 50,
Lyon 17, London 6, Bologna 114 -- and **76 are unresolved** (`k ≥ 2`, neither shown possible nor
shown impossible) -- Madrid 11, Lyon 5, London 1, Bologna 59.

#### T06 — Rebuild the four districts as `_r4` — completed 2026-09-03

**Artifacts:** `openubem/outputs/eu_evidence/EU-21/district_plans/{ES-MAD-BERRUGUETE,
FR-LYO-HAUTCOEURPENTES,GB-LDN-STDUNSTANS,IT-BOL-GALVANI2}_nocore_2026-09-03_r4.json` (four builds,
`python scripts/eu21/08_district_viewer.py --district <D> --tag 2026-09-03_r4 --generic-no-census`,
no `--overwrite`, `plans3D/index.html` untouched); matching
`docs/docs_ACTIVE/europeanLocations/plans3D/archive/PLANS_<D>_nocore_2026-09-03_r4.html` (four pages, archived 2026-09-03).
`scripts/eu21/08_district_viewer.py:568` (inside `build_html`'s `script_js`, the pop-up badge for a
`REFUSED_K_GT_12` plate): `<code>D-EU-65</code>` -> `<code>D-EU-92</code>`, text only, coordinator
instruction, outside T05's own file-layout scope (§3) but explicitly directed mid-task. All four
`_r4` pages then re-rendered from their already-built JSONs (`--render-only --overwrite`, JSONs not
touched, cutter not re-run) so the delivered pages carry the corrected badge text. **Not a `D-EU-85`
overwrite**: these four `_r4` pages had not been shown to the owner before this re-render -- the first
`--render-only` write already happened inside this same task, seconds after the `_r4` JSONs landed,
before any report reached the owner.

**Deviations:** two mid-task instructions from the coordinator, both executed as given, both text/wording
or measurement-only, no plan threshold or judge touched: (1) the `:568` `D-EU-92` wording fix above;
(2) the strip-bound falsification and withdrawal already logged under T05b.

**Test status:** PASS on every item of §6 T06's acceptance list.
`error = 0` in all four JSONs. `cutter_sha256` identical across all four
(`9a27c65fba56b78e6339165e483afec33295a0e8b750997280659b7d34b8169a`) and verified equal to the sha256
of `scripts/eu21/07_nocore_tests.py` on disk both before and after the `:568` wording fix (that fix
touched only `08_district_viewer.py`, never the cutter file) -- checked explicitly, not assumed.
`max_flat_aspect = 2.5` and `tag = "2026-09-03_r4"` in all four. Drawn 2,529 (>= `_r3`'s 2,521); PASS
2,178 (> `_r3`'s 2,012, strictly); refused 15 (<= 23, down from `_r3`'s 23 by exactly T05's 8 orange
recoveries). No-regression gate: **0 of 2,012 `_r3` PASS ids fail to read PASS in `_r4`**, checked
per district (Madrid 803, Lyon 247, London 50, Bologna 912 -- sums to 2,012) by loading both JSONs
directly and comparing `status`/`verdict` per `building_id`, not by re-running the bench. Page gates,
all four `_r4` pages (post `--render-only`): `Dwelling Index` count 1, `srcdoc` count 0,
`kwh|eui|energy|archetype` (case-insensitive) count 0, footer shows `2026-09-03_r4`, `D-EU-65` count 0,
`D-EU-92` present.

**Notes -- the Bologna 983-vs-982 discrepancy the coordinator asked to trace, not fix.** T04's own
bench (`colour_repair_bench_T04.json`) projected 71 Bologna FAIL->PASS recoveries (its `fail_set`
`changed_verdict` list intersected with Bologna's 292 `_r3` FAIL ids); the real `_r4` build recovered
70 (Bologna PASS 912 -> 982). The one plate accounting for the gap is **`building_id 29085`**
(COURTYARD group, `k = 1`). Reproduced directly (not inferred): `_bench_recut` on the `_r3`-stored
footprint returns **PASS** (`C6` contact 113.61 m), while `build_plate` on the raw manifest polygon
(`usable_polygon` + `centred`, exactly what the real district build calls) returns **FAIL** (`C6`
contact 0.00 m) -- both reproducible across repeated fresh-process runs, so this is not run-to-run
nondeterminism (§4.5 holds). Both starting polygons cut to the *same* 17-exterior-point, 1-ring
outline (the ring-bisection candidate wins in both cases, and `C5` passes in both) -- the divergence
is in which flat the search settles on relative to that outline, not in which candidate type wins.
The two starting polygons differ only at float-noise level (~2e-8 m² area, ~0.3 mm centroid: raw
manifest-derived vs `_r3`-stored-footprint-derived, since `_r3`'s old pre-T04 cutter never touched
this ring and stored it essentially unchanged) -- enough, evidently, to flip which candidate's flat
registers zero-vs-full contact against `poly.exterior` under `C6`'s 0.05 m buffer intersection. `29085`
was `FAIL` in `_r3` and is `FAIL` in `_r4` -- it never touches the no-regression gate. Not fixed, not
tuned, per instruction.

**CP-3.**

| district | census | drawn | PASS | FAIL | refused k>12 | error |
| --- | --- | --- | --- | --- | --- | --- |
| ES-MAD-BERRUGUETE | 961 | 955 (99.4%) | 867 (90.2%) | 88 | 6 | 0 |
| FR-LYO-HAUTCOEURPENTES | 297 | 295 (99.3%) | 264 (88.9%) | 31 | 2 | 0 |
| GB-LDN-STDUNSTANS | 82 | 75 (91.5%) | 65 (79.3%) | 10 | 7 | 0 |
| IT-BOL-GALVANI2 | 1204 | 1204 (100.0%) | 982 (81.6%) | 222 | 0 | 0 |
| fleet | 2544 | 2529 (99.4%) | 2178 (85.6%) | 351 | 15 | 0 |

Acceptance: all five items of §6 T06's list PASS (error 0; `cutter_sha256`/`max_flat_aspect`/`tag`
identical and correct across all four; drawn/PASS/refused all clear their bars; no-regression gate 0
of 2,012). Orange outcome (T05): 8 of 23 pass all seven at declared `k` (Madrid 1/7, Lyon 1/3, London
6/13, Bologna 0/0); 15 remain refused (`C10` 11, `C6` 6, `C11` 6); 0 raised, 0 timed out. `C11`
residual (T05b, `k = 1` argument, strip bound withdrawn): 187 of 263 forced by definition, 76
unresolved. Bologna's lone bench-vs-build discrepancy (`29085`) traced above, not a regression, not
fixed. 95% gate not evaluated (owner's call, `D-EU-91`); no EnergyPlus run.

#### T07 — D-EU-93: C11 does not apply to an undivided plate — completed 2026-09-03

**Artifacts:** three text/logic edits in `scripts/eu21/07_nocore_tests.py`, all exactly per §6 T07's
"How": (1) `run_checks`'s `C11` entry now reads `checks["C11"] = {"pass": True, "show":
f"{max_aspect:.1f} : 1 (k=1, D-EU-93)"}` when `len(live) <= 1`, unchanged otherwise (`max_aspect` still
computed and reported in both branches); (2) `_plate_score`'s `c11_ok = (len(live) <= 1) or (max_aspect
<= MAX_FLAT_ASPECT)`, the `-max_aspect` tie-break and every other returned tuple element untouched;
(3) `CHECK_META`'s `C11` row and `MAX_FLAT_ASPECT_STATUS` both extended with the `k = 1` exemption text
and a `D-EU-93` citation, text only. `MAX_FLAT_ASPECT` itself is unchanged at `2.5`. Output:
`openubem/outputs/eu_evidence/EU-21/rules_tests/colour_repair_bench_D_EU_93.json`.

**Deviations:** none from §6 T07's "How" 1-3. The bench (`--bench D_EU_93`) exceeded the director's
600 s foreground allowance and the tool moved it to background on its own (wall time 677.724 s,
consistent with T02-T04's 570-830 s range on the same 509+200-plate selection); it was not polled,
only read on its own completion notification.

**Test status:** PASS on the required gate. `colour_repair_bench_D_EU_93.json` control set: **200/200
PASS, 0 FAIL**, `fail_by_check` all zero (`C1` 0, `C3` 0, `C4` 0, `C5` 0, `C6` 0, `C10` 0, `C11` 0) — no
regression from the waiver. Fail-set (509, informational, same selection as T01-T04): pass 335, fail
174, `fail_by_check` `C1` 0, `C3` 0, `C4` 13, `C5` 30, `C6` 10, `C10` 54, `C11` 76 — `C4`/`C5`/`C6`/`C10`
unchanged from T04's rung, only `C11` moved (263 -> 76, i.e. -187, exactly T05b's forced-by-definition
`k = 1` count). `cutter_sha256` of the edited file on disk: `fe75c96ed0ad8512a72c93fccd27b7e46b05c325911163bb47e41b1932a85717`.

**Notes:** district rebuild run by the director.

#### T07 (rebuild) — the four districts as `_r5` — completed 2026-09-03 — **`CP-4` accepted**

**Artifacts:** `openubem/outputs/eu_evidence/EU-21/district_plans/<district>_nocore_2026-09-03_r5.json`
and `docs/docs_ACTIVE/europeanLocations/plans3D/PLANS_<district>_nocore_2026-09-03_r5.html`, four of
each. Run by the director sequentially, exit 0, wall time 219.6 s (London) to 512.7 s (Bologna); no
`--overwrite`, nothing existing was touched (`D-EU-85`).

**Deviations:** none.

**Test status:** all `CP-4` gates PASS.

| District | Census | Drawn | PASS | PASS % | 95 % bar | Refused | Error | `_r4` → `_r5` delta | Regressions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 961 | 955 | **916** | **95.3** | 913 — **crossed** | 6 | 0 | +49 | 0 of 867 |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 295 | 281 | 94.6 | 283 — 2 short | 2 | 0 | +17 | 0 of 264 |
| `GB-LDN-STDUNSTANS` | 82 | 75 | 71 | 86.6 | 78 — 7 short | 7 | 0 | +6 | 0 of 65 |
| `IT-BOL-GALVANI2` | 1,204 | 1,204 | 1,085 | 90.1 | 1,144 — 59 short | 0 | 0 | +103 | 0 of 982 |
| **FLEET** | **2,544** | **2,529 (99.4 %)** | **2,353** | **92.5** | 2,417 — 64 short | **15** | **0** | **+175** | **0 of 2,178** |

`fail_by_check`, fleet: `C1` 0 · `C3` 0 · `C4` 13 · `C5` 30 · `C6` 11 · `C10` 55 · `C11` 76. Every check
except `C11` is identical to `_r4`; `C11` alone falls 263 → 76. Per district: Madrid `C4` 1 / `C5` 5 /
`C6` 2 / `C10` 22 / `C11` 11; Lyon 1 / 5 / 1 / 3 / 5; London 0 / 0 / 0 / 3 / 1; Bologna 11 / 20 / 8 /
27 / 59. The measured **+175** matches the pre-build projection **district for district** (Madrid +49,
Lyon +17, London +6, Bologna +103).

Provenance gates: `cutter_sha256` =
`fe75c96ed0ad8512a72c93fccd27b7e46b05c325911163bb47e41b1932a85717` in all four JSONs, identical to the
edited file on disk; `max_flat_aspect` = **2.5** in all four; `tag` = `2026-09-03_r5` in all four;
`error` = 0 and no plate carries `status ERROR` in any district. Page gates: each of the four
`_r5.html` files carries the build tag, the cutter sha256 and the `(k=1, D-EU-93)` marker.

**Notes:** 🔴 **the 95 % gate is met** — Madrid at 95.3 %, and under `D-EU-91`/`D-EU-94` any one district
crossing opens it. This does **not** clear `D-EU-94` clause 3: `openubem/geometry/european_residential.py`
is still core-era, so no submission may follow from this result until the rules are carried into that
engine; `D-EU-54` is also still unconsumed. Per §6, this plan stops here and starts no EnergyPlus run
(`D-EU-55`). Recorded in `STATE` §3 and §8, `BRIEF` §6, `CHECKLIST`.
