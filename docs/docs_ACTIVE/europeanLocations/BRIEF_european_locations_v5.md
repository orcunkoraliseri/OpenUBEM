# European locations — the brief (v5)

🔴 **CLOSED 2026-09-09.** Closed, reopened the same day to harvest the 2026-09-08 recut, then closed
again once `T06b`, `T07` and `T08` of `implementation/PLAN_eu-recut-95pct-2026-09-08.md` landed. Read-only:
not executed, not appended to, not deleted. §2 below reads "Done, 2026-09-07" and is true only up to that
date. The final numbers — the four district EUIs, the fleet figure, and the delivered layout side-cars —
are in the block at the head of [`STATE_european_locations_v5.md`](STATE_european_locations_v5.md). Read
it before quoting anything from here.

---

<!-- superseded closure note, kept: -->
🔴 **CLOSED 2026-09-09 — owner ruling ("we have completed this project"). Read-only: not executed,
not appended to, not deleted.** §2 below still reads "Done, 2026-09-07" and is true only up to that
date; two further campaigns ran after it. The arc's final record — the last published EUI per district,
the 2026-09-08 recut that ran but was never harvested, and the three findings left open by ruling — is
the closure block at the head of [`STATE_european_locations_v5.md`](STATE_european_locations_v5.md).
Read that before quoting anything from here.

---

**2026-09-03.** One page: the goal, where it stands, the order of work.
All findings, rulings and numbers live in `STATE_european_locations_v5.md` — never here.

---

## 1. The goal

Four real European residential neighbourhoods — **Madrid Berruguete, Lyon Hauts de Croix-Rousse,
London St Dunstan's, Bologna Galvani 2** — every residential building modelled the published way:
real footprint, real storey count, each floor divided into residential thermal zones, each building
simulated on its own but surrounded by its real neighbours so shading is right.

A floor is divided into **dwellings only** — no circulation zone, no stair core, no corridor.

---

## 2. Where it stands

🔴 **Done, 2026-09-07.** All four steps in §4 below closed: the rule was written and proven, carried into
the engine (bit-parity, 0 mismatches), simulated on Speed (EU-11 ceiling82 harvest, four district EUIs),
and you read and confirmed the floor plans. The 3D viewers (`outputs_3D/eu_<district>_viewer.html`) now
show EUI colour and EU-21 PASS/FAIL badges on the same proven geometry. One item stays open, deliberately
not blocking closure: `FINDING 258` — a few plates split unevenly (tiny dwellings next to one oversized
one) despite passing all seven checks; your ruling was a per-building fix later, never a full-batch
re-cut. Full numbers: `STATE_european_locations_v5.md` §7, §8.

**Historical, kept for context.** The rest of this document (§3–§6) describes the arc as it stood while
still open, up to the 2026-09-04 log entries — read it for how the rule and the engine carry-in were
built, not for current status.

---

## 3. The work — `EU-20` and `EU-21`

**`EU-20`** sorts all 2,544 buildings into **eleven morphology groups** (courtyard, sliver, square,
rectangle, elongated rectangle, slab, triangle, parallelogram, L, U/T, complex multi-wing).

**`EU-21`** writes **one cutting rule per group** and grades it on **550 real plates** — 3, 6, 9 and 12
flats per floor imposed on every group, every plate drawn and scored. The deliverable is a document,
not a run: `rules/RULES_dwelling_layout_groups_nocore_*.html` plus the five sheets in `rules/tests/`.
**The document is the specification.**

Seven checks decide every plate:

| | What it forbids |
|---|---|
| `C1` | any square metre that belongs to no flat |
| `C3` | a sheet that claims more flats than it drew |
| `C4` | a flat in two pieces, or two flats overlapping |
| `C5` | a hole, a flat inside a flat, an outline over 40 points |
| `C6` | a flat with less than 2.50 m of **outer** façade |
| `C10` | anything narrower than 2.00 m — a pinch |
| `C11` | a flat more slender than the proportion limit — a ribbon |

---

## 4. The order from here

| | Package | What it does | Ends at |
|---|---|---|---|
| 1 | **`EU-21`** — write the rule | Eleven group rules, seven checks, 550 plates, `FAIL 0` | ✅ A rules document you have read |
| 2 | **engine** — carry it in | The written rule replaces the box-era logic, now in `european_nocore.py` | ✅ Bit-parity, 0 mismatches, 2,529/2,529 plates |
| 3 | **`EU-18`** — prove it | `plans3D/` republished; parity gate back to 0 | ✅ Your confirmation, 2026-09-07 (`D-EU-54`/`D-EU-105`), one named exception (`FINDING 258`) |
| 4 | **`EU-19`** — simulate | Four districts on Speed, harvest, viewers | ✅ Four fresh district EUIs, 2026-09-06 (London 97.08, Lyon 65.94, Madrid 77.15, Bologna 54.94 kWh/m²) |

**All four steps closed 2026-09-07.** Full closing detail — including the merge of EUI colour and EU-21
check badges onto the `outputs_3D/` viewers — is `STATE_european_locations_v5.md` §7 items 2–5 and §8's
final four entries.

---

## 5. Not in scope

Extending the typology table. The corridor / core path — **parked with its files intact**, only you may
restart it. No district EUI may be quoted until `EU-19` lands.

---

## 6. Progress log

Numbers are in `STATE_european_locations_v5.md` — this is the order of events only.

- **2026-09-01** — `EU-21` opened: eleven group rules written, 550 plates graded, no-core regime fixed
  (`D-EU-79`). The rule became the deliverable; the engine stopped being edited.
- **2026-09-02** — the seven checks frozen and calibrated; `MAX_FLAT_ASPECT` pinned at **2.5** (`D-EU-82`)
  and never moved since, through every proposal to move it.
- **2026-09-03 (morning)** — district viewers `_r2` built, then the `MultiPolygon` fault closed
  (`FINDING 243`): runtime errors 17 → **0**, no purple building anywhere. `_r3` rebuilt on the closed
  cutter; `_r2` archived on your sentence.
- **2026-09-03 (colour repair)** — broader angle search, reflex snapping, courtyard ring bisection, and the
  `k > 12` refusal demoted to an attempt (`D-EU-92`). Rebuilt as **`_r4`**, accepted at `CP-3`: `error = 0`
  in all four districts, no-regression **0 of 2,012**, 2,529 of 2,544 drawn.
- **2026-09-03 (`FINDING 245`)** — the 95 % gate measured **unreachable** while `C11` is applied to an
  undivided plate: 187 plates fail it at `k = 1`, where no cut was made. Put to you as `D-EU-93`.
- **2026-09-03 (`D-EU-93`, taken)** — *"yes lets go"*: `C11` is not evaluated at `k = 1`; the aspect is
  reported, not judged. Carried into the cutter and rebuilt as **`_r5`** — `CP-4`.
- **2026-09-03 (`D-EU-94`)** — *"once we reach 95, we will immediately start simulation on the speed
  cluster"*. The simulation gate is armed. The engine carry-in is now the only thing between the proven
  plans and that run.
- **2026-09-03 (`_r5`, accepted at `CP-4`)** — the four districts rebuilt on the `D-EU-93` cutter.
  **Madrid crosses the bar at 95.3 %** (916 of 961), three plates over. Lyon 94.6 %, Bologna 90.1 %,
  London 86.6 %; fleet 2,353 of 2,544 passing (92.5 %). Nothing else moved: same threshold, same cutter
  hash in all four, `error = 0`, no regressions against `_r4`.
- **2026-09-03 (the gate opens)** — one district at 95 % is what `D-EU-91` and `D-EU-94` asked for, so
  the simulation permission is now live. **It still cannot be used**: the engine that writes the IDFs is
  core-era, so a run today would simulate corridors and cores instead of these plans. The carry-in is the
  whole remaining critical path, and you have not yet read `plans3D/` (`D-EU-54`).
- **2026-09-03 (`D-EU-95`, the carry-in is running)** — *"lets go, to the end, no more ask, when you are
  satisfied, start simulations, i will go out"*. Taken as your own sentence for `D-EU-55`, conditional on the
  director being satisfied — which means the engine first. The rule set: the proven cutter is **copied**
  into the engine, never rewritten, and it is accepted only if it reproduces `_r5` **exactly** on all 2,544
  plates. Then the four districts' IDFs are rebuilt into new dated folders, audited to carry no circulation
  zone at all, and only then does the Speed campaign go out.
- **2026-09-04 (`FINDING 249`, `D-EU-99`, remedy)** — `CP-2` gate 5 failed on 1,306 interzone vertex reroutes;
  dedicated remedy plan `eu-nocore-finding249-remedy-2026-09-04` authorised. Restricted Option B remedy (partner-less
  near-duplicate-vertex carve-out) implemented and unit-tested (17/17 green). Local EnergyPlus 23.1.0 regression
  validation completed cleanly on 16/16 sample buildings (0 fatal, 0 severe).
- **2026-09-04 (`D-EU-100`, Speed campaign running)** — Gate-5 re-audit recovered 171 dwelling layouts (`FINDING 250`).
  Wait-for-`CP-2` gate lifted by your explicit order (`D-EU-100`). All 4 district fleets packaged, shipped to
  Speed (`/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_finding249_remedy_2026-09-04/`), and submitted in parallel
  using `sbatch --array=1-N%8 --time=7-00:00:00`: London (`1305158`, 82 tasks), Lyon (`1305167`, 293 tasks),
  Madrid (`1305176`, 952 tasks), Bologna (`1305186`, 1,200 tasks) — **2,527 tasks total, 32 active concurrent runs**.
- **2026-09-04 (London harvested & outputs_3D updated)** — London finished 100% clean (82/82 RC=0, mean EUI 87.34 kWh/m²).
  `outputs_3D/eu_GB-LDN-STDUNSTANS_viewer.html` and `buildings.csv` regenerated and mirrored. Fleet progress: 317 completed
  (Lyon 103, Madrid 65, Bologna 67, London 82), 24 running, 12 failed. Local monitoring stopped for your Antigravity
  update; cluster runs continue autonomously. Next session resumes at harvest.
- **2026-09-04 (viewer bug fixed, EUI colour mode added)** — the regenerated London viewer opened fully blank: a
  scene-JSON key mismatch (`provenance_counts` vs the viewer's `counts`) threw before anything drew. Fixed, and a
  new EUI colour mode + legend added so simulated heating demand is now visible on the map, not just height/age/
  provenance/layout-state. Applies to all 4 districts automatically.
- **2026-09-04 (`D-EU-101`, full-fleet expansion ruled)** — Owner: simulate every residential building regardless
  of type (house/apartment/terrace/generic), not just the flats-eligible census used so far. Real gap measured:
  London +1,160 (of 1,242 — currently only 82, all apartments/terrace; 1,018 single-family houses were never in
  scope), Lyon +237, Madrid +242, Bologna +20 — **+1,659 buildings total**, overwhelmingly a London problem.
  Blocker before launch (`FINDING 251`): the classification stage feeding the no-core cutter (`dwellings_total`,
  `storeys`) only covers the existing 2,544-building census — it doesn't exist yet for the gap population and must
  be built first. Current 2,527-task campaign completes first; expansion is the next arc.
- **2026-09-04 (`FINDING 251`, London fixed)** — 82 → 389 London buildings now classifiable (+307). Root cause:
  the code never mapped OSM's `house` tag to a building type at all — not a data gap, a code gap. First fix
  attempt (assume all houses are detached, `dwellings_total=1`) was wrong and caught before landing — a `house`
  tag can mean detached or mid-terrace, which behave very differently thermally. Correct fix splits by whether
  the footprint touches its neighbour (same method already used for Lyon/Bologna): all 307 recovered turned out
  to be terraced, none detached — checks out for that part of London. Madrid has the same gap, not yet fixed.
  London's remaining ~900 buildings are missing source data (no energy certificate on file, or an ambiguous
  build-date range) — a data problem, not a code one; needs your call on estimating vs. accepting the gap.
- **2026-09-04 (`FINDING 252`, full-fleet prep dispatched to Antigravity)** — corrected a stale CHECKLIST
  assumption (the gap population does not need `EU-20/morphology_census.csv`; cutting and IDF-writing are
  one step, not two). `PLAN_eu-nocore-full-fleet-expansion-2026-09-04.md` written and dispatched as a
  self-contained executor prompt: extend the GB fix to Madrid, re-run all four districts' IDF prep into new
  `_full_fleet_2026-09-04` folders (parallel to the live Speed campaign, never touching its files), audit,
  stop before packaging. Ready to submit the moment the current campaign drains.
- **2026-09-04 (`FINDING 253`, full-fleet prep T01-T03 complete, director-audited)** — Antigravity's report
  verified directly against the repo (diff + summary.json files), not taken on trust. Only the two planned
  files touched; live campaign folders untouched. London 82→389 (+307), Madrid 952→1,008 (+56), Lyon/
  Bologna unchanged (+0, as predicted). Fleet 2,527→2,890 (+363 of +1,659 gap). Stopped correctly before
  packaging. Still blocked on the live 2,527-task campaign draining (Lyon 122 / Madrid 708 / Bologna 1,063
  tasks remaining) before the expanded fleet can ship to Speed.
- **2026-09-04 (`FINDING 254`, remaining gap root-caused — no new fix found)** — investigated the residual
  1,296-building gap (4,186 attempted − 2,890 prepared). Three of four categories are genuine data gaps or
  documented fail-closed design (17 IDF crashes, Madrid/London 210 missing-storeys, London 800 no-EPC/period-
  straddle). The fourth — Lyon's 186 `TYPOLOGY_SIGNALS_DISAGREE`, 176 of which are ordinary 5–9-storey MFH —
  turns out to be the pre-existing unruled `D-EU-37` ("extend the typology table"), not a new question.
  Investigation closed; fleet holds at 2,890/4,186 (69 %) pending an owner ruling on `D-EU-37`.
- **2026-09-04 (`FINDING 255`, `D-EU-37` ruled and implemented)** — owner: *"100% full"* / *"make it
  possible"*. New bucket (`2<=dwellings<=12 & 5<=storeys<=9 -> MFH`) added to `derive_bdtopo_building_type`;
  Lyon's `prepare()` re-run, `population_prepared` 293→469 (+176, exact match to `FINDING 254`'s measurement).
  Fleet **2,890→3,066/4,186 (73.2 %)**. Remaining 1,120-building gap (9 categories, exact counts and code
  citations in `INVESTIGATION_full-fleet-100pct-2026-09-04.md`) handed to an owner-run external investigation
  (Gemini) rather than a further internal dispatch. Still blocked on the live 2,527-task Speed campaign
  draining before the expanded fleet packages and ships.
- **2026-09-04 (`FINDING 256`, London EPC construction-year recovery — +30)** — the full-fleet ceiling
  investigation found an observed `construction_year` already sitting in the cached UK EPC certificates and
  never read by `_gb_rows`. Plan `implementation/PLAN_eu-epc-construction-year-2026-09-04.md`, executed by two
  fresh Sonnet sessions and director-verified off disk at every step. New sidecar
  (`eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv` — 1,336 rows / 1,336 certificates /
  67 `osm_id`s) plus a new `_gb_age_decision` helper: a certificate year now supplies the period where RdSAP
  left no age band, and resolves a straddle where every observed year falls inside one TABULA period. Both
  stay fail-closed — contradicting or cross-period years are still refused. London `population_prepared`
  389→**419**; `MISSING_OBSERVED_EPC_AGE_BAND` 445→418, `PERIOD_STRADDLE_K_GB.07_GB.08` 20→12,
  `MISSING_OBSERVED_STOREY_COUNT` 47→52 (five footprints gain an age and then fail the *next* gate — bucket
  move, not a regression). Provenance stamped on exactly 30 rows (24 `EPC_OBSERVED_CONSTRUCTION_YEAR` +
  6 `EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE`); the other 389 blank. All 389 baseline buildings re-emit with
  **identical `idf_sha256`** — the fix is additive by measurement, not by assertion. Written to a *new* folder
  `GB-LDN-STDUNSTANS_full_fleet_epcyear_2026-09-04`; the baseline folder is untouched and promotion is
  deliberately left as a director decision. Fleet **3,066→3,096/4,186 (74.0 %)**. The ceiling itself is now
  published in `DEBUG_why-not-100-percent-2026-09-04.md`: 100 % is unreachable and ~3,430 (≈82 %) is the true
  maximum, because 418 London footprints have never had a certificate lodged at all and 269 more carry
  certificates that contradict one another. Still blocked on the live 2,527-task Speed campaign draining.
- **2026-09-06 (`EU-19` closed — the EU-11 ceiling82 harvest)** — all 10 Speed jobs drained and merged;
  3,344 run / 3,321 success / 23 failed (stop-condition 0.7 %, never tripped). Four fresh district EUIs:
  London 97.081151, Lyon 65.935928, Madrid 77.153998, Bologna 54.935569 kWh/m². Viewers regenerated on the
  harvested data.
  ⚠ Lyon's 65.935928 is **superseded** by the 2026-09-07 T07 restatement, **69.595307 kWh/m² over 505 of 509** (`EU-11/FR-LYO-HAUTCOEURPENTES_merged_2026-09-07/summary.json`), and London's 97.081151 by **120.064327 kWh/m² over 706 of 706** (`EU-11/GB-LDN-STDUNSTANS_merged_2026-09-07/summary.json`), and Madrid's 77.153998 by **80.694006 kWh/m² over 1,166 of 1,175** (`EU-11/ES-MAD-BERRUGUETE_merged_2026-09-07/summary.json`); Bologna is still the ceiling82 number and remains stale pending its delta harvest.
- **2026-09-07 (`D-EU-54`/`D-EU-105` closed)** — you read the merged `outputs_3D/` floor-plan modals and
  confirmed, with one named exception (`FINDING 258`, floor-plan division not homogeneous on some plates)
  carried forward as open work, not as a reason to keep the gate open.
- **2026-09-07 (viewer merge closed — the four-step order above is done)** — EU-11 EUI colour-by, EU-21
  zone colours, and EU-21 check badges all merged onto the same EU-17 geometry in
  `outputs_3D/eu_<district>_viewer.html`. Full numbers: `STATE_european_locations_v5.md` §8.
