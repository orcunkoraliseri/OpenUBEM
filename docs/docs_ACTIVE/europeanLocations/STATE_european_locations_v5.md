# European locations × Step 8 — arc state (v5)

**Opened:** 2026-09-03. **Scope of v5: the flat-division rules, under the no-core regime.** Everything
else in the arc is carried by pointer, not restated.

🔴 **v4 is superseded — this document is the read-first state of the arc.** v4 was written on
2026-08-31 around one question, *"relax the box rule in the engine and reach 95 % on the emitted IDFs"*.
That question is not dead but it is **not the live front**: since 2026-09-01 the arc works on the
**rules themselves**, on 550 real plates, with a direct cutter that is independent of the engine
(`EU-20`, `EU-21`). Since 2026-09-02 night it does so **without any circulation zone** (`D-EU-79`).
`previous/STATE_european_locations_v4.md`, `previous/BRIEF_european_locations_v4.md` and
`previous/CHECKLIST_european_locations_v4.md` (moved 2026-09-03) are historical from that moment: not
executed, not appended to, not deleted.

- Plain-language brief: [`BRIEF_european_locations_v5.md`](BRIEF_european_locations_v5.md)
- Progress checklist, work-package view: [`CHECKLIST_european_locations_v5.md`](CHECKLIST_european_locations_v5.md)
- 🔴 **Operating prompt for the live front** — read this before touching anything in `EU-21`:
  [`prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md`](prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md)
- Arc-local error index (`D-EU-52`): [`debugs/DEBUG_REFERENCES_european_locations.md`](debugs/DEBUG_REFERENCES_european_locations.md)
- Live rules (no-core): [`rules/`](rules/) — the four `*_nocore_*` documents; core versions in `rules/archive/`.
- History: `previous/` (v2, v3, v4 states and briefs, MVP, walkthrough).

**This document carries current truth only.** Replace an entry when it stops being current; never append
below it.

---

## 0. Identifier bookkeeping — read before allocating anything

The arc has claimed **`D-EU-49` … `D-EU-110`** and **`FINDING 211` … `FINDING 263`**
(`FINDING 215`–`219` were never allocated — skip them, do not backfill).
**Next free: `D-EU-113`, `FINDING 268`.** (`D-EU-111`, `D-EU-112` and `FINDING 267` are allocated by `implementation/PLAN_eu-recut-95pct-2026-09-08.md`, 2026-09-08.)

⚠ **`D-EU-106`–`109` are lettered rulings taken 2026-09-07 inside the three second-wave plan docs and
registered here by filename, provenance only** (the plan doc is the authority, this ledger only reserves
the number): `D-EU-106` and `D-EU-109 a`…`g` in
`implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md`; `D-EU-107 a`…`g` in
`implementation/PLAN_eu-plan-homogeneity-2026-09-07.md`; `D-EU-108 a`…`f` in
`implementation/PLAN_eu-london-coverage-2026-09-07.md` (Options 2+3 admission ruled in
`debugs/docs/DECISION_REQUEST_D-EU-108_london_recovery_2026-09-07.md`). `FINDING 259`–`263` live in the
same three docs; `FINDING 262` (232 of 344 imbalanced plates are also undivided, so the landing order
`D-EU-109` → `D-EU-107` → `D-EU-108` is load-bearing) and `FINDING 263` (the near-duplicate-vertex path is
non-deterministic, so every hash gate must exclude and name that population) are the two that constrain
later work.

⚠ **`D-EU-102`–`104` were claimed in `implementation/PLAN_eu-82pct-ceiling-2026-09-05.md` (T03's stop
and T07a/b's authorization) and never registered back here — this ledger under-counted them until
2026-09-07.** Re-registering by filename, not by re-deriving new numbers, to avoid a collision: they stay
with the ceiling82 plan, provenance only. `D-EU-105` is the first number this ledger actually allocates
past that gap (§8, 2026-09-07).

Where the rulings live: `D-EU-49`…`D-EU-58` in `previous/STATE_european_locations_v4.md` §4 ·
`D-EU-59`…`D-EU-63` in `prompts/previous/DIRECTOR_PROMPT_european_locations.md` ·
`D-EU-64`…`D-EU-78` in `prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` §2 and §5
(**parked path — provenance only**) · `D-EU-79`…`D-EU-100` in §4 below · `D-EU-102`…`D-EU-104` in
`implementation/PLAN_eu-82pct-ceiling-2026-09-05.md` (provenance only) · `D-EU-105` in §8 below.

---

## 1. What may be quoted, and what may not

🔴 **The S0 quotable perimeter is unchanged and is not reopened by v5**: 149 marker-free certified cells,
`it` = **108.25 kWh/m² ± 0.16 %** heating-only (measured on 35 of the 74), `uk` withheld at fold level,
`es` never quotable, no cell-level number, every `f`-difference carrying both perimeters (92 / 149),
peak-and-timing claims only. The full bar table is v2 §1 — still binding, unedited.

🔴 **No `S2` district EUI may be quoted.** The embargo carries forward unchanged: `FINDING 211`
(ruled coverage far below the 95 % bar), `FINDING 212` (the refusal is a morphology refusal),
`FINDING 213` (the viewer and the simulated IDF describe different buildings), `FINDING 214` (the EUI
denominator never moved to conditioned area). None of the four is closed. It lifts when a resimulation
lands on plans that have been seen and proven — `EU-19`, which has not started.

🔴 **No number produced by `EU-20` / `EU-21` is a district number.** The 550 test plates are real
footprints, but they are a **rule bench**, not a fleet census: they measure whether a rule cuts a plate
correctly, not how many buildings carry a plan. Never quote a test-sheet PASS count as coverage.

⚠ Bologna carries `construction_period_provenance = IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on
**100 %** of rows. Never quote a Bologna number without it.

🔴 **As of 2026-09-08, one of the four published `EU-11` ceiling82 district EUIs (Bologna 54.935569
kWh/m²) is still stale and may not be quoted as current.** Madrid has been restated at T07:
**80.694006 kWh/m² over 1,166 of 1,175 buildings**
(`openubem/outputs/eu_evidence/EU-11/ES-MAD-BERRUGUETE_merged_2026-09-07/summary.json`), replacing
77.153998 — a **+3.540008 kWh/m²** move; `eui_source` counts `final_2026-09-07` 272,
`delta_2026-09-07` 664, `ceiling82_carry` 230, `pending_resimulation` 9, no disclosures. Lyon has been
restated at T07: **69.595307 kWh/m² over 505 of 509 buildings**
(`openubem/outputs/eu_evidence/EU-11/FR-LYO-HAUTCOEURPENTES_merged_2026-09-07/summary.json`), replacing
65.935928; `eui_source` counts `final_2026-09-07` 91, `delta_2026-09-07` 159, `ceiling82_carry` 255,
`pending_resimulation` 4. London has been restated at T07 as well: **120.064327 kWh/m² over 706 of 706
buildings** (`openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_merged_2026-09-07/summary.json`),
replacing 97.081151 — a **+22.983176 kWh/m²** move, the largest of the arc so far; `eui_source` counts
`final_2026-09-07` 299, `delta_2026-09-07` 37, `ceiling82_carry` 370, `pending_resimulation` 0, so unlike
Lyon the London number carries no pending population and no disclosure. Two disclosures ride with that number: stem `cee45cbc2718154c` was rebuilt from
29 dwelling zones to 8 `one_zone_per_floor` zones with the courtyard filled, so its floor area and EUI
denominator differ from every earlier manifest; and the 4 `pending_resimulation` buildings carry no result
columns at all rather than an EUI from a different IDF (`FINDING 265`).
`D-EU-107`, `D-EU-108` and `D-EU-109` are in execution against a merged re-emission
(`openubem/outputs/eu_evidence/EU-11/<DISTRICT>_final_2026-09-07/`); the `*_ceiling82_2026-09-05/` trees
are superseded and read-only, never overwritten
(`implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md:341`). *"The four published EUIs …
become stale the moment this lands — no district EUI may be quoted between T05 submission and T06's
restatement"* (`implementation/PLAN_eu-plan-homogeneity-2026-09-07.md:266-267`); every district EUI moves
and is restated once, at T07, with both the pre-fix and post-fix populations named
(`implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md:235-238`, `D-EU-109 d`). Lyon and London
were restated 2026-09-07; Madrid and Bologna are still pending their `_delta_2026-09-07` harvests.

---

## 2. Work packages

| WP | What it is | Status |
|---|---|---|
| `EU-01` … `EU-12` | TABULA loader → results and dossier → district campaign → viewer + pop-up | Completed |
| `EU-13` / `EU-14` / `EU-13B` / `EU-14B` | Layout coverage, Bologna construction year, ruled grid, layout binding | Completed |
| `EU-15` | Ruled thermal zoning to the ≥ 95 % bar | Completed 2026-08-30 — **bar not met** (`FINDING 211`) |
| `EU-16` | 20 m context geometry, adiabatic party walls, four-district resimulation | Stopped 2026-08-31 (`D-EU-53`) — context landed, resimulation cancelled |
| `EU-17` / `EU-17a` / `EU-17b` | Relax the box rule in the engine; fallback tier (`D-EU-58`) | Completed 2026-09-01 — **the bar it aimed at is still not met**, see §3 |
| `EU-18a` / `EU-18b` | `plans3D/` pages + parity gate | Completed 2026-09-01 — pages exist; **the gate exits 1**, see §3 |
| `EU-18c` (T13) | Non-box EnergyPlus sample battery | 🔴 Blocked on the owner's own sentence (`D-EU-55`) |
| `EU-19` | Four-district resimulation on proven plans | In progress — running in parallel on Speed (Jobs 1305158, 1305167, 1305176, 1305186) |
| **`EU-20`** | **Morphology atlas: the eleven building groups, 2,544 rows** | **Completed 2026-09-01** |
| **`EU-21`** | **The flat-division rules: one written rule per group, graded on 550 real plates** | **In progress — the live front** |
| `D-EU-106` | Repaint `outputs_3D` floor-plan modal in the `plans3D` visual style | Completed 2026-09-07 |
| `D-EU-107` | Balance the dwelling cut (`C12`), re-plan/re-simulate the affected plates only | In progress — `CP-1`/`CP-2`/`CP-3` parity half signed, `CP-3` hash half unsigned |
| `D-EU-108` | London coverage recovery (terrace-row age/storey inheritance) | In progress — complete through T05b; harvest/final restatement pending |
| `D-EU-109` | Recover discarded dwelling divisions (ring cleanup); merges `D-EU-107`/`D-EU-108`/`D-EU-109` into one re-emission and one Speed campaign | In progress — merged re-emission (T03m) running for `ES-MAD`/`IT-BOL`, Speed campaign not yet submitted |

*Status is one of Completed / In progress / Not started / Blocked. This table carries no notes.*

---

## 3. Open items

### 🔴 `FINDING 211` / `212` / `213` / `214` — carried, none closed

Measured 2026-08-31 on the artefacts and restated in full in `previous/STATE_european_locations_v4.md`
§3. Summary: ruled coverage 56.92 % against a 95 % bar; 43.1 % of the fleet refused at layout time and
61.1 % actually simulated as an undivided box; 459 buildings drawn in the viewer with a plan their IDF
does not carry; the EUI denominator equal to gross area on 2,544 of 2,544 rows.

### 🔴 `EU-17` did not lift coverage, and `EU-18b`'s gate does not return zero

Measured by T12 on the `EU-17` tree, 2026-09-01, with `is_ruled()`'s **broad** definition (includes
`DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT`):

| District | ruled | of | ruled % | bar |
|---|---:|---:|---:|---|
| `ES-MAD-BERRUGUETE` | 194 | 961 | **20.19 %** | FAIL |
| `FR-LYO-HAUTCOEURPENTES` | 105 | 297 | **35.35 %** | FAIL |
| `GB-LDN-STDUNSTANS` | 17 | 82 | **20.73 %** | FAIL |
| `IT-BOL-GALVANI2` | 225 | 1,204 | **18.69 %** | FAIL |

`scripts/eu18_parity_gate.py` returns **exit 1, 970 divergent buildings** (ES 463, FR 91, GB 21,
IT 395) — the same `FINDING 213` reroute mechanism, reproduced building-for-building on the fully
recovered 2,544/2,544 population, plus a Madrid-only `STOREY_COUNT_MISMATCH` class on 29 rows. Nothing
in T05–T15 targeted either. **This is why the arc pivoted**: the engine cannot be repaired before the
rule it is supposed to implement is written down and proven. That is `EU-21`.

Population and conservation are, by contrast, sound: 2,544/2,544 buildings retained (`D-EU-58` fallback
tier), 0 single-storey cores, 0 area-conservation violations at 1 × 10⁻⁶, 0 named-reason exclusions.

### 🟢 `EU-21` no-core rules lift census drawn coverage from 21.3 % to 98.5 % (clearing the 95 % bar) and cadastral coverage to 99.0 %

Measured 2026-09-03 across all four district evidence JSONs (`EU-21/district_plans/<district>_nocore_2026-09-03_r2.json`) and the then-active 3D viewers (`plans3D/archive/PLANS_<district>_nocore_2026-09-03_r2.html` — archived 2026-09-03; superseded by `_r3`, `_r4`, `_r5`):

**1. Census Fleet Progress (2,544 buildings — formal 95 % evaluation denominator, bar = 2,417):**

| District | Census Rows | Before (EU-17 IDFs) | Now: Drawn | Now: Passing All 7 Checks | 95 % Bar Target | Status |
|---|---:|---:|---:|---:|---:|---|
| `ES-MAD-BERRUGUETE` | 961 | 194 (20.2 %) | **946 (98.4 %)** | 871 (90.6 %) | 913 | PASS |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 105 (35.4 %) | **293 (98.7 %)** | 277 (93.3 %) | 283 | PASS |
| `GB-LDN-STDUNSTANS` | 82 | 17 (20.7 %) | **69 (84.1 %)** | 53 (64.6 %) | 78 | *(13 refused k > 12)* |
| `IT-BOL-GALVANI2` | 1,204 | 225 (18.7 %) | **1,197 (99.4 %)** | 1,034 (85.9 %) | 1,144 | PASS |
| **FLEET TOTAL** | **2,544** | **541 (21.3 %)** | **2,505 (98.5 %)** | **2,235 (87.9 %)** | **2,417** | **CLEARS BAR (+88)** |

**2. Full Cadastral Fleet Progress (All 4,186 buildings across the 4 European locations):**

| District | Cadastral Total | Census Drawn | Generic Fallback (Dark Green) | Total With Floor Plan | % With Interior Flats |
|---|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 1,194 | 946 | 233 | **1,179** | **98.7 %** |
| `FR-LYO-HAUTCOEURPENTES` | 530 | 293 | 233 | **526** | **99.2 %** |
| `GB-LDN-STDUNSTANS` | 1,242 | 69 | 1,159 | **1,228** | **98.9 %** |
| `IT-BOL-GALVANI2` | 1,220 | 1,197 | 16 | **1,213** | **99.4 %** |
| **FLEET TOTAL** | **4,186** | **2,505** | **1,641** | **4,146** | **99.0 %** |

**Key achievements:**
- **Census floor division:** Rose from **21.3 %** (541 buildings) to **98.5 %** (2,505 buildings), exceeding the 95 % threshold by 88 buildings. 2,235 buildings (87.9 %) pass all seven geometric checks simultaneously.
- **Generic fallback:** 1,641 uncatalogued manifest buildings (previously left as undivided massings) now carry generic morphology-based dwelling layouts (`D-EU-90`) styled dark green (`rgb(24, 94, 46)`).
- **Zero unpartitioned massings:** 4,146 of 4,186 total structures (99.0 %) across all four districts now carry an interior floor plan partition.

**🔴 Superseded by `_r3`, 2026-09-03 — the tables above are the `_r2` build and must not be quoted as current.**
`_r3` (`EU-21/district_plans/<district>_nocore_2026-09-03_r3.json`, cutter sha256 `76a124bfda43…`,
`MAX_FLAT_ASPECT = 2.5`, `error = 0` in all four) is the build made against the closed compactness
cutter, and it is the one to quote:

| District | Census | Drawn | Drawn % | PASS all 7 | PASS % | Refused | Error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 961 | 954 | 99.3 | 803 | 83.6 | 7 | 0 |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 294 | 99.0 | 247 | 83.2 | 3 | 0 |
| `GB-LDN-STDUNSTANS` | 82 | 69 | 84.1 | 50 | 61.0 | 13 | 0 |
| `IT-BOL-GALVANI2` | 1,204 | 1,204 | 100.0 | 912 | 75.7 | 0 | 0 |
| **FLEET** | **2,544** | **2,521 (99.1 %)** | | **2,012 (79.1 %)** | | **23** | **0** |

Cadastral fleet with an interior partition: **4,163 of 4,186 (99.4 %)** (1,642 generic). Drawn rises by
16 against `_r2` — the `FINDING 243` fix removed all 17 `error` buildings — while PASS falls from 87.9 %
to 79.1 % because `C10` became the `D-EU-87` opening test and `MAX_FLAT_ASPECT` moved 4.0 → 2.5 by
ruling. **The fall is a stricter ruler, not a worse cut**, and the residual is `FINDING 242`. Fleet
failing checks: `C11` 291 · `C10` 168 · `C5` 74 · `C4` 13 · `C6` 11 · `C1` 0 · `C3` 0.

**🔴 Superseded in turn by `_r4`, 2026-09-03 later the same day — quote this table, not `_r3`'s.**
`_r4` (`EU-21/district_plans/<district>_nocore_2026-09-03_r4.json`, cutter sha256 `9a27c65fba56…`,
`MAX_FLAT_ASPECT = 2.5` **unchanged**, `error = 0` in all four) is the `eu21-colour-repair` build,
accepted at `CP-3`:

| District | Census | Drawn | Drawn % | PASS all 7 | PASS % | Refused | Error |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 961 | 955 | 99.4 | 867 | 90.2 | 6 | 0 |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 295 | 99.3 | 264 | 88.9 | 2 | 0 |
| `GB-LDN-STDUNSTANS` | 82 | 75 | 91.5 | 65 | 79.3 | 7 | 0 |
| `IT-BOL-GALVANI2` | 1,204 | 1,204 | 100.0 | 982 | 81.6 | 0 | 0 |
| **FLEET** | **2,544** | **2,529 (99.4 %)** | | **2,178 (85.6 %)** | | **15** | **0** |

Fleet failing checks, `_r4`: `C11` 263 · `C10` 55 · `C5` 30 · `C4` 13 · `C6` 11 · `C1` 0 · `C3` 0.

🔴 **The rise from 79.1 % to 85.6 % moved no threshold.** The same seven checks at the same values judged
both builds; `MAX_FLAT_ASPECT` is 2.5 in each. What changed is the *candidate search*: more cut bearings
(long-edge and reflex-bisector directions), reflex-vertex boundary snapping, courtyard-ring bisection at
low `k`, and — per `D-EU-92` — the `k > 12` plates being cut and judged instead of refused unmeasured
(8 of 23 passed; one at `k = 31`). **No-regression gate: 0 of the 2,012 `_r3` PASS plates fails in `_r4`**,
checked id by id, which is the guarantee that the gain is a better cut and not a looser ruler.

⚠ One bench/build divergence, recorded not repaired: Bologna `29085` (a `k = 1` ring) is `PASS` in the
`T04` bench (`C6` 113.6 m) and `FAIL` in the real build (`C6` 0.00 m). It is a bench fidelity artifact on
ring plates, not a regression — the plate was `FAIL` in `_r3` too.

**🔴 Superseded in turn by `_r5`, 2026-09-03 — this is the build to quote. `_r4` is history.**
`_r5` (`EU-21/district_plans/<district>_nocore_2026-09-03_r5.json`, cutter sha256
`fe75c96ed0ad8512c72c93fccd27b7e46b05c325911163bb47e41b1932a85717` — **identical in all four** —
`MAX_FLAT_ASPECT = 2.5` **unchanged and never moved**, `error = 0` in all four) is the `D-EU-93` build,
accepted at `CP-4`:

| District | Census | Drawn | Drawn % | PASS all 7 | PASS % | 95 % bar | Gap | Refused | Error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `ES-MAD-BERRUGUETE` | 961 | 955 | 99.4 | **916** | **95.3** | 913 | **+3 over** | 6 | 0 |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 295 | 99.3 | 281 | 94.6 | 283 | 2 short | 2 | 0 |
| `GB-LDN-STDUNSTANS` | 82 | 75 | 91.5 | 71 | 86.6 | 78 | 7 short | 7 | 0 |
| `IT-BOL-GALVANI2` | 1,204 | 1,204 | 100.0 | 1,085 | 90.1 | 1,144 | 59 short | 0 | 0 |
| **FLEET** | **2,544** | **2,529 (99.4 %)** | | **2,353 (92.5 %)** | | **2,417** | **64 short** | **15** | **0** |

Fleet failing checks, `_r5`: `C11` 76 · `C10` 55 · `C5` 30 · `C4` 13 · `C6` 11 · `C1` 0 · `C3` 0.
**Every check except `C11` is unmoved from `_r4` count-for-count**; `C11` alone falls 263 → 76, which is
the whole of the `D-EU-93` effect and the proof that nothing else was touched.

🔴 **The 95 % gate is met. Madrid passes 916 of 961 census plates = 95.3 %, three plates over its bar of
913.** Under `D-EU-91`/`D-EU-94` **any one** district crossing opens the gate, read on `PASS` over
`census_rows`. The measured PASS delta is **+175 fleet-wide (Madrid +49, Lyon +17, London +6, Bologna
+103) — exactly the pre-build projection, district for district**, which is the strongest available
evidence that the ruling did what it was scoped to do and nothing more.
**No-regression gate: 0 of the 2,178 `_r4` PASS plates fails in `_r5`**, checked id by id in all four
districts. Drawn is unchanged at 2,529; refused unchanged at 15; `error = 0` ×4; no `ERROR` status
anywhere in the fleet. Page gates: all four `PLANS_<district>_nocore_2026-09-03_r5.html` carry the build
tag, the cutter sha256, and the `(k=1, D-EU-93)` marker on the card.

⚠ **This opens the simulation gate. It does not clear the engine blocker** (`D-EU-94` clause 3):
`openubem/geometry/european_residential.py` is still core-era, so a campaign submitted now would simulate
core-and-corridor layouts rather than these plans. The carry-in is the critical path, and `D-EU-54` — the
owner reading `plans3D/` — is still unconsumed.

### 🔴 `FINDING 238` — a check set that scores no shape term certifies ribbons

Measured by the director 2026-09-03, directly on the five stored `test_0N_nocore.json`: the no-core
regime's `FAIL 0` was arithmetically correct against its six checks and said nothing about the drawings.
Over 550 plates / **3,267 flats**, slenderness = long/short of the flat's minimum rotated rectangle:

| slenderness | flats above | plates with ≥ 1 |
|---|---:|---:|
| > 2.0 | 2,196 (67 %) | 366 / 550 |
| > 2.5 | 1,849 (57 %) | 296 |
| > 3.0 | 1,577 (48 %) | 240 |
| > 3.5 | 1,358 (42 %) | 205 |
| > 4.0 | 1,217 (37 %) | 178 |

Worst plates, all at k = 12: `COURTYARD` 29659 **14.12** · `L_SHAPE` `way/391279228` 13.58 ·
`COMPLEX_MULTI_WING` 31801 13.02 · `TRAPEZOID` `way/391662735` 12.90 · `TRIANGLE` `way/389587830` 12.80 ·
`U_OR_T_SHAPE` 32131 11.63 · `SQUARE` `way/391279229` 11.54.

Cause, isolated to one line: `build_flats` (`scripts/eu21/07_nocore_tests.py:533`) keeps the single-axis
cut whenever `_fully_ok` passes, and neither `_fully_ok` nor `_plate_score` carries a shape term, so the
grid cutter is only ever reached by plates that already failed something else. `C10` forbids a **pinch**
and is satisfied by a 2 m × 40 m ribbon. **Remedy is `D-EU-82`/`D-EU-83`/`D-EU-84`, §4 below, in flight.**

### 🔴 `FINDING 239` — a builder that hard-codes a delivered filename destroys the delivered file

Recorded by the director 2026-09-03 at the `CP-1` audit of `eu21-compactness`. `run_test`
(`scripts/eu21/07_nocore_tests.py:1041`) builds its output path as a literal
`..._nocore_2026-09-02.html`, so every ordinary `--test N` run of the repair plan rewrote the
**delivered** 2026-09-02 sheet in place. Three of the five were overwritten at 08:54 on 2026-09-03 by the
`T01`–`T04` run commands: `TEST_01_three_per_group`, `TEST_03_five_per_group`,
`TEST_05_ten_per_group`. They are untracked by git and unrecoverable; the files still named `2026-09-02`
now carry post-`T04` drawings. Only `TEST_02_floor_sizes_x3` and `TEST_04_floor_sizes_x5` are still the
authentic delivered sheets.

**What is not lost.** The measured evidence. All five `test_0N_nocore.json` were snapshotted byte-exact
into `rules_tests/baseline_nocore_2026-09-02/` before the first edit and verified by `sha256` at `T01`;
every number quoted in `FINDING 238` is re-derivable from them. The loss is the drawings of the
superseded build, which `EU-21` supersedes anyway. **Remedy is `D-EU-85` below.**

**Second occurrence, 2026-09-03 ~09:53.** The `T05b` executor ran `--test all` before `T05c` had repointed the
output tag, so all five owner-read `TEST_0*_nocore_2026-09-03.html` in `rules/tests/` were rewritten with
post-`T05b` drawings. This time nothing is lost: the byte-exact copies in `rules/tests/archive/reviewed_2026-09-03/`
are restored into `rules/tests/` as step 0 of the resumed `T05b`, and the tag is repointed to `_r2` before any
further run. The lesson of `D-EU-85` is restated: the repoint is the **first** edit of a repair plan, not a step
inside a later task.

### 🔴 `FINDING 240` — the residual ribbons are the cutter's choice, not the footprint's constraint

`T05` ran the `D-EU-84` ladder over all 550 plates and **no rung reached `FAIL 0`**: 2.5 -> 51 fails,
3.0 -> 24, 3.5 -> 17, 4.0 -> 11. The residual at 4.0 is 11 plate-appearances over **7 buildings, every
one at `n = 12`, only in the two size-imposed tests**: `COURTYARD 28125` 6.8:1, `COURTYARD 29659`
14.1:1, `COURTYARD 31169` 5.1:1, `L_SHAPE way/290026256` 5.0:1, `L_SHAPE way/391279228` 6.7:1,
`COMPLEX_MULTI_WING way/968439455` 4.7:1, `COMPLEX_MULTI_WING 31312` 5.6:1.

The obvious excuse — that a thin ring or wing physically cannot hold a compact flat — was tested by the
director and **is false.** Measured on the live JSONs, the local band width of the plate under each
offending flat (largest disc inscribed in the plate, centred anywhere inside the flat) is
**8.2 - 16.4 m**, while the flat's own short side is **2.05 - 3.50 m**: the flat occupies **13 - 32 %**
of the width the footprint offered it. Flat areas are ordinary (48 - 72 m²) — a 59 m² flat in an 8 m
band fits as 7.7 x 7.7 m. `COURTYARD 29659` is the extreme: ten of its twelve flats are 2.06 m strips
inside a band up to 16.4 m wide, and its 14.12:1 is **unchanged from the pre-`C11` baseline**, which
means the grid-first path of `D-EU-83` never won that plate.

So the residual is a **cutter defect on three group rules**, not a geometric impossibility, and not a
reason to touch the limit. Remedy is `D-EU-86` below.

### 🔴 `FINDING 241` — `C10` reported the *widest* place in a flat, so it certified necks under 2 m

The owner read the 2026-09-03 sheets and marked four plates with a red box — `COMPLEX_MULTI_WING`
Bologna 29965, `COURTYARD` Bologna 32052, `COURTYARD` Bologna 30127, `COURTYARD`
Bologna 28754 — every one of them a flat squeezed to a neck of well under two metres beside a notch or a
light well, and every one of them printed **`C10 4.0 m` PASS**.

`C10` was wired to `widest_fit` (`scripts/eu21/04_group_tests.py:299`), which walks
`NARROW_PROBES_M` from the top and returns the **first** probe `w` where `zone.buffer(-w/2)` is still
non-empty. That is the **largest** disc the flat can hold, capped at 4.0 m. It answers "is this flat fat
**somewhere**", and the plate line then took `min` of that over the flats
(`07_nocore_tests.py:705-706`). A flat 10 m x 8 m with a 0.4 m neck at one corner returns 4.0 m and
passes. The constant `4.0` appearing on card after card is the probe ceiling, not a measurement.

**Director's measurement, all 550 baseline plates, morphological opening at `r = 1.00 m` with mitre
joins (so a clean polygon loses exactly nothing):**

| | |
|---|---|
| plates holding at least one sub-2 m region | **182 of 550 (33 %)** |
| flats holding one | **278 of 3,267 (9 %)** |
| of that area, **inherited** from the plate's own tips and slots | 175 m² (11 %) |
| of that area, **created by the cut** | **1,349 m² (89 %)** |
| flats whose *created* pinch exceeds 0.10 m² | **279** |

The area distribution is cleanly bimodal — 2,686 flats at exactly zero, 254 under 0.01 m² of float
noise, 80 in a thin 0.01 – 0.50 m² band, then 247 above 0.50 m² — so a tolerance is a choice about noise,
not about how much pinching is acceptable.

This is `FINDING 238` a second time: a check that prints a ceiling certifies whatever it cannot see.
Nine of ten pinched square metres are the cutter's own doing. Remedy is `D-EU-87` below.

### 🔴 `FINDING 242` — after `D-EU-87`, no rung of the ladder reaches `FAIL 0`; the residual is a ring/wing family

Measured by the `T05c` executor and re-derived by the director from the stored `test_0N_nocore.json`
(2026-09-03, cutter sha `d1fa6bd0…`): `TOTAL FAIL` 81 / 62 / 46 / 39 of 550 at `MAX_FLAT_ASPECT` 2.5 / 3.0 /
3.5 / 4.0; 511 PASS / 39 FAIL at 4.0 over 26 distinct buildings (`COURTYARD` 9, `COMPLEX_MULTI_WING` 7, two
each `L_SHAPE` / `SLIVER` / `TRIANGLE` / `U_OR_T_SHAPE`, one `CORRIDOR_RECTANGLE`, one `SLAB`). `C10`
residual at 4.0: 15 buildings, worst `COURTYARD 29659` at 34.11 m² of cut-created pinch on a 1.78 m band.
The `D-EU-87` fix itself works: fleet created-pinch 1358.78 → 134.63 m² (−90 %), plates over the 0.10 m²
tolerance 184 → 33 of 550, three of the owner's four marked plates now `PASS`, zero regression on
`C1/C3/C4/C5/C6`. What remains needs a cutter that can segment a ring or a wing **around** a void or a
notch; `cut_layered` (across a band's depth) and `_donate_the_neck` (a pinch piece to a neighbour) are both
already at work and both fall short there. Remedy is `D-EU-89` clause 2.

### 🔴 `FINDING 243` — 17 census buildings raise inside `build_flats`; the 550 test plates never showed it

The district run (`D-EU-88`, cutter shas `6715a017…` / `18e6a49d…`) ends 8 Madrid, 1 Lyon and 8 Bologna census
buildings in `status = ERROR`, token `CUT_AttributeError`: `'MultiPolygon' object has no attribute
'exterior'` (5) / `'interiors'` (11), plus one `TopologyException: unable to assign free hole to a shell`
on Bologna that may already be the `_opening_lost` case fixed at 11:00. Groups: `COMPLEX_MULTI_WING` 6,
`COURTYARD` 4, `SLIVER` 6, `SLAB` 1; `k` from 3 to 12. None of the 550 test plates raises it, so the five
sheets under-cover the fleet on exactly the operation the sheets certify. Remedy is `D-EU-89` clause 3:
the district JSONs join the acceptance.

### 🔴 `FINDING 244` — runaway leftover absorption on non-convex shapes creates extreme flat area disparities

Identified 2026-09-03 by the owner on the 3D viewer (`way/428478249` U-shape, `way/391276770` complex multi-wing) and measured by the director across the Madrid fleet: parallel column slicing across multi-wing or re-entrant footprints cuts through multiple disconnected wings simultaneously. Because thermal zoning (`C4`) forbids MultiPolygons, `_seed_flats` takes only the single largest piece for each flat column, leaving all fragments in secondary wings as orphans. Under rule `D-EU-80`'s leftover absorption, all orphan pieces in an adjacent wing merge together and donate whole to whichever single flat touches that wing.

**Measured on Madrid (`ES-MAD-BERRUGUETE`):**
- In `way/428478249` (U-shape, $k=7$): flats D1–D6 are 24–30 m² while D7 swallows the entire bottom wing, reaching **299.8 m²** (ratio **12.5 : 1**).
- Generic fallback buildings ($k > 1$): **59 of 99 buildings (60 %)** have max/min area ratio $> 1.30$; worst `way/403642586` reaches **14.3 : 1** (10.5 m² vs 149.6 m²).
- Census buildings ($k > 1$): **297 of 654 buildings (45 %)** have max/min area ratio $> 1.50$, and 15 exceed $7.0 : 1$ (worst `way/435633561` at **12.4 : 1**, 35 m² vs 434 m²), yet all were certified `PASS` because no rule scored flat area spread.
- In `way/391276770` (complex multi-wing), all 12 flats have equal net area (78.7 m²), but single-axis slicing across angled wings stretches Flat D7 across a $17.4\text{ m} \times 21.8\text{ m}$ bounding box with high pinch area ($7.23\text{ m}^2$), producing visual sprawl.

Cause: `DD-C` / `DD-4` previously made equal area purely informational to unblock width checks, leaving the engine with zero protection against runaway absorption. Remedy is an area balance gate (e.g. `C12`, max/min ratio $\le 2.0$) and multi-wing/grid cutting for non-convex morphologies.

### 🔴 `FINDING 245` — the 95 % gate (`D-EU-91`) is unreachable in every district while `C11` is applied at `k = 1`

Measured 2026-09-03 by `PLAN_eu21-colour-repair-2026-09-03.md` `T05b`, after `T02`–`T04` had recovered 160 of
the 509 `_r3` `FAIL` plates (`colour_repair_bench_T04.json`). Of the **263** plates still failing `C11`
(slenderness, `MAX_FLAT_ASPECT = 2.5`), **187 have `k = 1`**: Madrid 50, Lyon 17, London 6, Bologna 114.

**At `k = 1` there is no partition to choose.** The single flat *is* the plate, so `flat_aspect` is a property
of the footprint the cutter is handed, not of the cut it makes. No search improvement, no candidate, no angle
and no ruling short of changing `MAX_FLAT_ASPECT` itself can move one of these 187 plates. This is a definition,
not an estimate.

**Arithmetic ceiling per district** — census plates minus the `k = 1` `C11` failures alone, i.e. the number
reached only if *every other* remaining failure in that district were repaired:

| district | census plates | `k = 1` `C11` | ceiling | `D-EU-91` gate |
| --- | --- | --- | --- | --- |
| `ES-MAD-BERRUGUETE` | 961 | 50 | ≤ 911 = **94.8 %** | not reachable |
| `FR-LYO-HAUTCOEURPENTES` | 297 | 17 | ≤ 280 = **94.3 %** | not reachable |
| `GB-LDN-STDUNSTANS` | 82 | 6 | ≤ 76 = **92.7 %** | not reachable |
| `IT-BOL-GALVANI2` | 1,204 | 114 | ≤ 1,090 = **90.5 %** | not reachable |

The true figure is below each ceiling, because the `k ≥ 2` `C11` failures (76 fleet-wide, **unresolved** — not
shown to be fixable) and the `C10` / `C5` / `C4` / `C6` residuals are all still failing.

🔴 **A bound was proposed here and falsified; do not revive it.** `T05b` first classified the 263 with a strip
bound (`A / k > 2.5·w²`, `w` = twice the largest-inscribed-circle radius), giving 175 forced / 88 not forced.
Run against the 200-plate control set — every member of which already passes `C11`, so every member demonstrably
*has* a conforming partition — the bound wrongly called two of them forced (`way/288447771` aspect 1.17,
`way/311431849` aspect 1.01; `colour_repair_bench_C11FALSIFY.json`). The inscribed-circle probe underestimates
achievable width on non-convex footprints. **The 175 / 88 split is withdrawn and must never be quoted.** The
187 / 76 split above rests on the `k = 1` argument alone and is unaffected.

**This is a decision for the owner, not a defect to fix.** `D-EU-84` and `D-EU-86` bar the director and every
executor from loosening a rung, and `D-EU-91`'s condition was the owner's own sentence. Either the gate is met
below 95 %, or `C11`'s application at `k = 1` is ruled on, or the campaign does not run. No one may resolve this
by moving `MAX_FLAT_ASPECT`.

### 🔴 `FINDING 246` — the district census cuts **one** `k` per building; the engine cuts **one `k` per storey**, and for 81 % of the fleet those are not the same number

Found by the director 2026-09-03 while writing the engine carry-in plan, before any code was written. This is a
**scope** difference between the accepted review artifact and the thing that will be simulated, not a defect in
either.

- **What the census does.** `08_district_viewer.py:146` sets `k = r["_n"]`, and `_n` is
  `max(1, round(dwellings_total / storeys))` (`01_cut_group_plans.py:154`) — **a single per-floor count for the
  whole building**, cut once on a footprint that has been `usable_polygon`-repaired and then **`centred`**
  (translated so its centroid is the origin, `04_group_tests.py:206`).
- **What the engine does.** `generate_european_building_dwelling_layout:2585` takes
  `floor_allocations` from `allocate_european_dwellings`, which conserves the declared dwelling total exactly:
  `storeys` get `tot // storeys`, and the first `tot % storeys` of them get one more. So a building with a
  remainder is cut at **two** distinct counts, `q` and `q + 1`, and it carries floor plans only if **both** pass.
- **How many.** Measured on `EU-20/morphology_census.csv`, all 2,544 rows. The operative count is buildings whose
  allocation contains **more than one distinct dwelling count**, i.e. that the engine cuts twice:
  **1,814 of 2,544 (71.3 %)** — Madrid 524/961 · Lyon 184/297 · London 68/82 · Bologna 1,038/1,204.
  (`dwellings_total % storeys != 0` holds for 2,064, but where the quotient is 0 it clamps to 1 and the two
  counts collapse; **quote 1,814**.) The `> 12` refusal barely moves: only **2 buildings** (both Madrid) reach
  `> 12` on the engine's larger count while the census's single `k` stayed `<= 12`; 23 buildings have census
  `k > 12` already.
- **The dwelling totals themselves agree, by construction.** `morphology_census.csv`'s `dwellings_total` is read
  from the engine's own layout side-cars (`eu20_morphology_atlas.py:149-154`, `EU-17/<district>/layouts/*.json`),
  which come from `allocate_european_dwellings`. So the census and the engine agree on **how many dwellings a
  building has**, including the imputed ones; they differ **only** in how those dwellings are spread over storeys.
  That is what makes this a bounded, measurable difference rather than an open question.
- **Consequences, stated plainly.**
  1. **`_r5`'s 2,353 PASS is a per-plate number, not a per-building prediction of the IDF outcome.** It says the
     cutter can serve *that* storey at *that* count. It does not say the building's other storey count also
     passes, and for 81 % of the fleet there is another one.
  2. **`_r5` is not dwelling-conserving and was never meant to be.** `k × storeys` need not equal
     `dwellings_total`; the engine's allocation does equal it, and conservation is an existing hard invariant
     (`tests/geometry/test_eu13b_dwelling_conservation.py`, `EU-13B` `T01`/`T02`). **The engine must not be
     changed to match the census here** — that would trade a real guarantee for a cosmetic match.
  3. Neither may `k` be clamped, rounded or redistributed to make the two agree (`D-EU-88` clause 1).
  4. The cutter is also fed a **centred** polygon by the census and a **raw UTM** polygon by the engine. The
     carry-in must centre the plate before cutting and translate the flats back, or `set_precision`'s millimetre
     grid lands on different bits at 4.5 × 10⁶ m than at the origin.
- **What this does *not* change.** The `D-EU-91`/`D-EU-94` gate was defined, ruled and met on the district census
  as measured — Madrid 916/961 = 95.3 %. That reading stands; this finding does not reopen it. What it changes is
  the *acceptance test of the carry-in*: the engine's own building-level census is measured separately
  (`PLAN_eu-engine-nocore-carryin-2026-09-03.md` `T05a`) and reported as its own number, never silently
  substituted for the census figure and never quoted in its place.

### 🔴 `FINDING 247` — the cutter's winning candidate is not uniquely determined at millimetre input precision, and a verdict can flip on it

**Measured 2026-09-03**, directly, on the accepted `_r5` build and its extraction.

`build_flats` chooses among its candidate partitions by a strict `>` over a score tuple that is itself rounded to
three decimals — `07_nocore_tests.py:970`:

```python
return (cov_ok, c5_ok, c6_ok, c4_ok, c11_ok, round(-pinch_total, 3), round(min_c6, 3), round(-max_aspect, 3))
```

When two **structurally different** candidates land inside that 1 mm band, which one wins is decided by input
precision below a millimetre. This is not a rounding artefact in the score; it selects a different partition.

- `way/232618736` (Madrid, `k = 3`): the candidate the census chose is `rows = 1`, flats 108.72 / 110.42 /
  112.14 m². Perturb the input at the millimetre and the winner becomes `rows = 2`, flats 82.82 / 82.82 /
  165.63 m² — a visibly different plan. Both pass the seven checks, so the **verdict** is unaffected here.
- `way/391270221` (Madrid, `k = 5`): the same perturbation flips the **verdict itself**, `FAIL` → `PASS`.

**How it was found.** The first `CP-1` parity run fed the cutter the footprint stored in the `_r5` JSON, and got
1 verdict / 53 check / 51 geometry mismatches out of 2,529 plates (2.1 %). Re-run against the census's real
input, all four counts go to **0**.

**The mechanism is not a serialization loss — the storage is lossless.** Checked directly: all 14,116 stored
Madrid footprint coordinates lie exactly on the millimetre grid, because the cutter's output is `set_precision`-
snapped to `RING_STABILIZATION_GRID_M = 0.001` before it is written. What is stored is the cutter's **output
plate**, which is a mm-snapped, `_normalize`d transform of the census's full-precision **input** polygon. Feeding
the output back in is therefore a real ≤ 1 mm perturbation of the input — enough to move a candidate across the
3-decimal score band, but nothing to do with how the file was written.

**What this means, and what it does not.**
1. The extraction is **not** implicated — the mismatches came from the harness's input, and that is fixed
   (`PLAN_eu-engine-nocore-carryin-2026-09-03.md` `T02` §1).
2. The published `_r5` figures are **reproducible** — the same input gives the same answer, every time. Nothing
   about 2,529 drawn / 2,353 PASS is retracted.
3. But they are **not stable to millimetre-scale footprint noise**. About 2 % of plates sit close enough to a
   score tie that a 1 mm change of input geometry moves their plan, and a small number of those move their
   verdict. So: never quote `_r5` as invariant under a change of footprint source, reprojection, or
   round-tripping through a serialized format. If the fleet's geometry is ever re-derived — a different OSM
   snapshot, a different CRS, a re-export — the census must be re-run, not carried over.
4. **This is not to be "fixed" by widening the tie band, by adding a deterministic tie-break, or by any other
   change to the cutter.** `D-EU-95` binds: the carry-in is an extraction, and the extraction must reproduce
   `_r5` including this behaviour. Recorded here so it is known, not so it is repaired.

### 🔴 `FINDING 248` — the failing plates are **not** being "pushed to divide": every `C5` failure is an **undivided** plate. But 107 census buildings are almost certainly not residential

**Measured 2026-09-03**, on the owner's question, against `morphology_census.csv` and the accepted `_r5` JSONs.

The owner pointed at `IT-BOL-GALVANI2` / `30090` in `PLANS_IT-BOL-GALVANI2_nocore_2026-09-03_r5.html` and
asked whether the arc is forcing non-residential buildings to divide like residential ones.

**On the mechanism, the answer is no — that building is not divided at all.**

- `30090`: area 5,393 m² · 13 storeys · **16** declared dwellings · `idf_state` `RULED` · 70 denoised
  vertices. `dwellings_total / storeys` rounds to **`k = 1`**, so the plate is drawn whole, one dwelling per
  storey, and the only failing check is **`C5`** — 90 outline points against the ≤ 40 cap. `C1` 100.0 %,
  `C4` 0.00 m², `C10` 0.00 m², `C11` 1.7 : 1 `(k=1, D-EU-93)` all pass. No division rule touched it.
- Fleet-wide the same holds: **every `C5` failure in `_r5` is a `k = 1` plate** — Madrid 5 of 5, Lyon 5 of 5,
  Bologna 20 of 20, London 0 of 0. `C5` measures footprint outline complexity, never flat division.
- And the failing side is not the low-density side. Median GFA per declared dwelling, `PASS` vs not-`PASS`:
  Madrid 85 / 52 · Lyon 77 / 62 · London 30 / 12 · Bologna 89 / 82 m². The failures sit at *higher* dwelling
  density, not lower. The 416 plates carrying > 200 m² GFA per dwelling fail at 11.1 % (46 of 416) against the
  fleet's 7.5 % (191 of 2,544) — slightly worse, but they are only 46 of the 191 failures. Exempting the
  low-density buildings would leave 145 failures standing; it is not where the residual lives.

**On the substance, the owner's observation is real, and it is a simulation problem, not a coverage problem.**

- **107 of 2,544 census buildings (4.2 %) carry more than 500 m² of gross floor area per declared dwelling** —
  Madrid 50 · Bologna 47 · London 8 · Lyon 2. `30090` carries **4,382 m² per dwelling** (70,109 m² GFA / 16).
  No dwelling is 4,382 m². These are non-residential or mis-tagged buildings that entered the universe at
  **EU-02**, in `openubem/outputs/eu_evidence/EU-02/<district>/02_residential_manifest.gpkg` — the file
  `01_cut_group_plans.py:139` reads and every downstream census inherits.
- 85 of the 107 **pass** all seven checks, so they are invisible in the coverage figures and will be simulated
  as apartment blocks with one enormous dwelling per storey.

**Would excluding them lift the coverage? Measured — no.** The owner asked directly (2026-09-03). Dropping the
low-density buildings from the census and recomputing `PASS / drawn`:

| district | base | drop > 1000 m²/dw | > 500 | > 300 | > 200 |
|---|---|---|---|---|---|
| Madrid | 916/961 **95.3 %** | 900/942 95.5 % | 870/911 95.5 % | 835/876 95.3 % | 782/821 95.2 % |
| Lyon | 281/297 **94.6 %** | 281/296 94.9 % | 280/295 94.9 % | 275/289 95.2 % | 253/265 95.5 % |
| London | 71/82 **86.6 %** | 67/78 85.9 % | 63/74 85.1 % | 61/72 84.7 % | 61/72 84.7 % |
| Bologna | 1085/1204 **90.1 %** | 1077/1186 90.8 % | 1055/1157 91.2 % | 977/1071 91.2 % | 887/970 91.4 % |

The best case is **+1.3 points** (Bologna, and only by dropping 234 buildings — 19 % of the district). **London
goes down** at every threshold, because its low-density buildings pass more often than its dense ones. Lyon
crosses 95 % only at `> 200 m²/dw`, a cut that also discards genuinely residential stock. The exclusion is
**not** a route to the 95 % bar, and `D-EU-96` retired that bar in any case.

**And OSM cannot identify them.** The manifest carries `building_tag` / `function_tag`, and on the census
universe they are: Madrid `apartments` / `house` / `detached` / `residential`; Lyon `Résidentiel` plus **6**
`Commercial et services`; London `house` / `apartments` / `residential` / `terrace` plus 4 singletons
(`student_accommodation`, `dormitory`, `retirement_home`, `fast_food`); **Bologna is 1,202 of 1,220 rows tagged
`Edificio generico`** — the Italian source carries no use information at all. `30090` is `Edificio generico`.
So the district that motivated the question is exactly the one where no tag-based filter exists; any exclusion
would have to be a **density heuristic**, i.e. a new modelling assumption, not a data filter.

**What this does not license.** No filter is added to the cutter, no check threshold moves, and no delivered
number is retracted — `D-EU-96` retired the 95 % bar, so nothing here changes a published figure. The fix, if
one is ordered, belongs **upstream at the EU-02 manifest**, not in `european_nocore.py`. Whether the 107 are
excluded from the campaign, simulated as-is and flagged in the results, or left alone is an **owner decision**
and is not taken here.

### 🔴 `FINDING 249` — `CP-2` FAILS. The cutter succeeded on 831 more plates, and the IDF assembler threw away 1,306 of them: the no-core dwelling layouts do not survive `intersect_match`

**Measured 2026-09-03**, by the director, on the four rebuilt district trees
`openubem/outputs/eu_evidence/EU-11/<DISTRICT>_nocore_2026-09-03/`, against the delivered core-era build in
`EU-11/<DISTRICT>/` and against `T05a`'s census. Audit artifact:
`openubem/outputs/eu_evidence/EU-21/engine_parity/idf_audit_2026-09-03.json`.

**Four of the five `CP-2` gates pass, and pass exactly.**

- **Zero `*_circulation` zones** in all four `idfs/` trees — the plan's first 🔴 gate. The corridor path really is
  gone from the emitted IDFs.
- **The route counts equal `T05a`'s `EMITTED` to the building.** `real + rerouted + IDF_ASSEMBLY_FAILED` =
  Madrid 278+618+9 = **905** · Lyon 157+119+4 = **280** · London 22+40+0 = **62** · Bologna 499+529+4 = **1032**;
  fleet **2,279 = 2,279**. Fallback 265 = `T05a`'s `REFUSED_K_GT_12` 25 + `FALLBACK` 240. `FINDING 246`'s oracle
  holds with no slack.
- **`conditioned_floor_area_m2 == floor_area_m2`** for every one of the 2,262 emitted-family buildings, worst
  relative deviation **0.0000**.
- **The old-vs-new `prepared_buildings.csv` diff is clean row for row** — `archetype_id`, `building_type`,
  `age_band` mismatch **0 / 0 / 0** in all four districts, on 2,527 common buildings, and **no new building
  appears**. This was the mandatory live-API contamination check for Bologna
  (`opendata.comune.bologna.it`, fetched uncached). It passes.

**The fifth gate fails, and it is the one the whole carry-in exists for.**

| | delivered (core-era) | rebuilt (no-core) |
|---|---|---|
| real dwelling layouts | **1,446** | **956** |
| `..._INTERZONE_MISMATCH_REROUTED` | **2** | **1,306** |
| `FALLBACK_PENDING_LAYOUT*` | 1,096 | 265 |
| `IDF_ASSEMBLY_FAILED_RuntimeError` | 0 | 17 |
| rows written | 2,544 | 2,527 |

Per district, real dwelling layouts: Madrid **614 → 278** · Lyon **198 → 157** · London **40 → 22** ·
Bologna **594 → 499**. Rerouted: Madrid 618 · Bologna 529 · Lyon 119 · London 40.

**The cutter got much better and the assembler could not consume it.** Fallback collapses 1,096 → 265: the
extracted no-core cutter divides 831 plates the core-era logic refused. But `FINDING 210`'s safety net —
`find_mismatched_interzone_pairs` + `_force_reroute_room_layout_to_one_zone_per_floor`, wired into
`scripts/run_eu_s2_campaign.py::build_idf_for_building` — fires on **1,306** of them, because geomeppy's
`intersect_match` leaves unresolved interzone vertex mismatches on the finer subdivision. When it fires the
dwelling layout is **discarded** and the building is rebuilt as **one whole-building zone per storey**.
Net: **−490 real dwelling layouts against the build already delivered.**

**Verified in the IDFs, not inferred from the label.** Sampled five real and three rerouted stems per district.
Real carry `_F<n>_dwelling_<k>` zones (Bologna `387f4fea` 30, Lyon `a3fabf61` 29, London `ed827c95` 69);
rerouted carry only `_F<n>_whole` — Madrid `959c9188` 3 zones / 3 whole, Lyon `197fe0f9` 7 / 7,
Bologna `1ef46361` 7 / 7. **Zero `_dwelling_` zones in any rerouted building.**

**Why this stops the submission.** The `geometry_outcome` column labels all 1,306 `DWELLING_LAYOUT_EMITTED_…`,
so a campaign launched now would report 2,279 buildings as carrying emitted dwelling layouts while **57.7 % of
them are per-floor massing with no dwelling subdivision at all** — and would do so on *fewer* real layouts than
the build already on disk. That is precisely what `D-EU-95`'s `CP-2` was written to catch. **`D-EU-98`
clause 2 applies: nothing is submitted. No `sbatch` has been issued and the Speed queue is untouched.**

**Two probes, neither explains it.** Rerouted vs clean on Madrid: `k = 1` share 27.8 % vs 41.5 %, median `k` 2
vs 2; median footprint vertices 6 vs 5, storeys 4 vs 4, reflex vertices 1 vs 0, rectangularity 0.847 vs 0.880.
Footprint complexity leans the right way but separates nothing cleanly. The mechanism is inside
`intersect_match`'s vertex handling, not in the cut geometry, and finding it is the next task — **not** a
threshold move, and **not** a relaxation of `NEAR_DUPLICATE_VERTEX_TOLERANCE_M`.

**Also newly lost: 17 buildings** to `IDF_ASSEMBLY_FAILED_RuntimeError` (Madrid 9, Lyon 4, Bologna 4, London 0)
where the delivered build lost none. They get no IDF at all. Second-order beside the 1,306, but real.

**How this nearly passed, and why the audit must be read this way.** The T05 executor measured everything above
correctly and still concluded `CP-2` should be signed, reporting the gate-2 gap as **−17**. Two things hid the
1,306: the `geometry_outcome` prefix `DWELLING_LAYOUT_EMITTED…` puts the rerouted buildings inside the emitted
bucket in every count, and the 80-building dwelling-conservation sample was drawn **only** from buildings whose
IDF already carries `_dwelling_` zones — so it reads 80/80 while saying nothing about the 1,306 that carry none.
Neither is dishonest; both are invisible unless the reroute **rate** is compared against the delivered build.
`CP-2`'s wording should be read as requiring that comparison in future: an outcome label is not evidence that
the layout reached the IDF. The executor's per-building measurements are preserved unchanged in
`idf_audit_2026-09-03.json`; the director's `cp2_verdict` block was added beside them, not over them.

### 🔴 `FINDING 250` — restricted Option B remedy recovers only 171 of the 1,306 rerouted buildings; `CP-2` gate 5 still FAILS

**Measured 2026-09-04**, by the director, directly from `prepared_buildings.csv` in the four freshly rebuilt
trees — not from any agent's report — while `PLAN_eu-nocore-finding249-remedy-2026-09-04.md`'s `T04` was still
in progress. `T01`/`T02` of that plan (the restricted remedy: only the partner-less near-duplicate-vertex
carve-out, interzone-paired defects still reroute unconditionally — `D-EU-99`'s `CP-1` pick) are done and
unit-tested (17/17 green). The four districts were rebuilt fresh into
`openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/`, never overwriting the
`_nocore_2026-09-03` baseline.

| | `_nocore_2026-09-03` baseline (`FINDING 249`) | `_finding249_remedy_2026-09-04` |
|---|---:|---:|
| real dwelling layouts | 956 | **1,127** (+171) |
| `..._INTERZONE_MISMATCH_REROUTED` | 1,306 | **1,135** (−171) |
| reroute rate | 57.7 % | **50.2 %** |
| fallback | 265 | 265 (unchanged) |
| `IDF_ASSEMBLY_FAILED_RuntimeError` | 17 | **17 (unchanged)** — this remedy never touched that code path |
| emitted-family total | 2,262 | 2,262 (= `T05a`'s 2,279 − 17, gate 2 still exact) |

Per district (real → real, reroute → reroute): Madrid 278→389, 618→506 · Lyon 157→171, 119→105 ·
London 22→22, 40→40 (no partner-less defects there) · Bologna 499→544, 529→484.

**Verdict: `CP-2` gate 5 still FAILS.** The restricted remedy is correctly scoped and does exactly what it was
designed to do (recover only the partner-less population, per `D-EU-99` `CP-1`), but that population is a small
minority of the defects — the reroute rate barely moves (57.7 % → 50.2 %) and stays nowhere near the delivered
build's 2-building baseline. Per the remedy plan's own `T04` hard rule, this is the reportable result, not a
license to invent a further remedy. Evidence:
`openubem/outputs/eu_evidence/EU-11/*_finding249_remedy_2026-09-04/prepared_buildings.csv`.

**Not yet closed.** `T03` (16-building real-EnergyPlus regression check on the sample, including the
partner-less-excused buildings) was still running at the time of this measurement — 0 Fatal/0 Severe confirmed
on the first 14/16 so far, no regression seen. It gates nothing above; these audit numbers come from a full
static re-derivation of `geometry_outcome` across all 2,262 emitted-family buildings and do not depend on it.

**What this means for `D-EU-100`.** `D-EU-100` already lifted the "wait for `CP-2` to re-pass" gate on the
owner's own explicit, repeated order — so this `FAIL` does **not** block `T06`/Speed submission. It is recorded
here because a measured result is not optional bookkeeping regardless of whether it still blocks anything: the
1,306→1,135 reroute population, if simulated, still yields `one_zone_per_floor` massing for roughly half the
fleet, not the no-core dwelling layout — that must be reported honestly alongside any campaign result, not
absorbed into an "EMITTED" label the way `FINDING 249`'s own near-signature already warned against (§3 above,
"How this nearly passed").

**Root cause of the residual 1,135, not yet investigated**: interzone-paired defects (the majority) still
reroute unconditionally by `D-EU-99` `CP-1`'s own design — `T05-fix` (root-cause `intersect_match` itself, and
recover the 17 `IDF_ASSEMBLY_FAILED_RuntimeError` buildings) remains **owner's call, not started**
(`CHECKLIST_european_locations_v5.md`).

### ⚠ Carried unchanged, not re-measured

`G8.0` FAIL 99/121, `G8.1`–`G8.4` NOT SCOREABLE, `FINDING 181`, `184`, `198`, `199`, `205`, `210`
(and its `D-EU-43` residual), `FINDING 215` (Madrid storey-count class), `FINDING 220` (closed by
`D-EU-58`'s fallback tier). `D-EU-37` ruled 2026-09-04 (`FINDING 255`) — see §5 "Gates that need the owner".
`FINDING 225`–`230` belong to the **parked** corridor path and are provenance, not open work.

---

## 4. The regime in force

Everything in this section is what an executor obeys today. The corridor path — `D-EU-64`…`D-EU-78`,
the `C2`/`C7`/`C8`/`C9`/`R2` checks, `05_group_cutters.py`, plan `eu21-cutter` — is **parked with its
files intact** (`D-EU-79`). Do not restart it; only the owner may.

**`D-EU-79` — the no-core regime** (owner 2026-09-02: *"i have decided with nocore option for all,
becasue core is getting complex everything"* · *"no more core options, only nocore options, lets go, it
is easier to handle."*). A plate is divided into **dwellings only**. No circulation zone, no core, no
corridor is drawn, and no rule, check or sheet refers to one.

**`D-EU-80` — no empty space per floor** (owner: *"no empty space per floor, add these empty spaces
inside the closest falt (at that case no need to create equal floor area flat zones)"*). Every square
metre belongs to exactly one flat; leftover area is absorbed into the flat it touches most. Equal flat
areas are **not** required and never justify a gap. Scored by `C1 = 100.0 %`.

**`D-EU-81` — nothing narrower than 2 m** (owner: *"violation of this global rule Nothing narrower than
2 m"*). No flat may contain any part narrower than 2.00 m, measured as the widest disc that fits.
Scored by `C10 ≥ 2.00 m`.

**`D-EU-82` — a flat has a proportion limit** (owner 2026-09-03: *"we are dviding flat zones but there
could be a limit to a width of a flat, i do not know. you define and add to the global rules, becasue in
the examples i am givigin to you as you can see a lot of narrow flats are available."* — the limit is
the director's to define). A flat's **minimum rotated rectangle** may not exceed `MAX_FLAT_ASPECT` in
long/short ratio. Scored by the new check **`C11`**. `C10` forbids a pinch; `C11` forbids a ribbon; both
are printed on every sheet. The value is a module constant, calibrated by `D-EU-84`, never a per-group
exception.

**`D-EU-83` — division from the second edge is first-class** (owner: *"why not adding division from
second edge … you are dicviding from one edge, but instead we can define a rule"*). Every `rows × cols`
scheme, on **both** bearings, is a candidate for **every** plate, scored against the same checks as the
single-axis cut. A grid is not a rescue for plates that failed; it competes from the start.

**`D-EU-84` — the limit is calibrated against the plates, not asserted.** `MAX_FLAT_ASPECT` is the
**strictest** rung of `{2.5, 3.0, 3.5, 4.0}` that still reaches `FAIL 0` on all 550 plates. If no rung
reaches it, the executor **stops** and the director rules — an exemption is never invented, and no
threshold is ever loosened to lift a census.

**The regime scores seven checks and only seven:** `C1` coverage · `C3` drawn = claimed flat count ·
`C4` one room per flat, no overlap · `C5` simple outline, ≤ 40 points, no interior ring · `C6` ≥ 2.50 m
of **outer** façade per flat · `C10` ≥ 2.00 m width · `C11` ≤ `MAX_FLAT_ASPECT` proportion.
`C2`, `C7`, `C8`, `C9` and `R2` are circulation checks and are **removed** from the sheets entirely,
not printed as `N/A`.

**Carried from before the pivot and still binding:** ceiling **12 flats per floor** (`D-EU-65`); 9–10
cut on the `6x2` grid with column merges (`D-EU-66`); above 12 refuses by design. Test numbers 3 / 6 /
9 / 12 are flats per floor imposed on every group.

🔴 **`D-EU-55` stands, unweakened: no EnergyPlus run of any kind without the owner's own sentence.**
A relayed "continue", an approved plan or a signed checkpoint is not permission. Writing geometry is
fine; running it is not.

🔴 **Never regenerate or overwrite a delivered artifact** (owner 2026-09-02: *"do not ever update
anything unless i say so"*). Every build takes its own dated filename; the reviewed one is never
touched.

🔴 **`D-EU-85` — a builder script may never write to a delivered dated filename.** The output date
in a generator is repointed to the new build date as the **first** edit of any repair plan, before a
single run command is issued; a plan that leaves it pointing at the delivered build has already lost it.
Ruled 2026-09-03 after `FINDING 239`. This is the operational half of the never-overwrite rule above:
the rule is not kept by intention, it is kept by the path in the code.

---

🔴 **`D-EU-86` — `C11` is not relaxed and no plate is exempted; the three failing group rules
are fixed instead.** Ruled at `CP-2`, 2026-09-03, on the director's own measurement (`FINDING 240`).
The ladder found no rung at `FAIL 0`, and `D-EU-84` sends that to the director. The ruling:

1. **No exemption, no named-building list, no loosened rung.** An 11-plate carve-out is exactly the
   invented exemption `D-EU-84` forbids, and the footprint excuse has been measured and refuted.
2. **`MAX_FLAT_ASPECT` stays unfrozen at the ladder's own answer.** The constant is set only once the
   cutters reach `FAIL 0`, and then to the **strictest** rung of 2.5 / 3.0 / 3.5 / 4.0 that does — the
   ladder is re-run after the fix, never inherited from the failing run.
3. **A cut may never spend less than half the width the footprint offers.** Where the plate's local band
   is `w` and the flat's area is `a`, a flat whose short side is under `w/2` while a compact division
   was available is a cutter defect by construction. The three group rules at fault — `COURTYARD`,
   `L_SHAPE`, `COMPLEX_MULTI_WING` — must divide a **thick** band across its depth as well as along its
   run, and the grid-first candidate of `D-EU-83` must be able to win a courtyard ring, which today it
   cannot.
4. **The plate score decides, and it must prefer the compact candidate.** If a compliant division exists
   and the cutter returns a ribbon, the fault is in `_plate_score`, not in the limit.

🔴 **`D-EU-87` — `C10` measures the narrowest place a cut creates, never the widest place a flat
happens to have.** Ruled 2026-09-03 on the owner's four marked plates and the director's census
(`FINDING 241`).

1. **`widest_fit` is disqualified as a verdict.** It may still be printed as a descriptive number; it may
   never decide `C10`, and it may never be the quantity a score maximises.
2. **The new `C10` is an opening test.** For each flat `f`, erode by `r = 1.00 m` and dilate back, both
   with **mitre** joins, and take the area of `f` that the opening does not return. That area is, by
   construction, the part of the flat narrower than **2.00 m**.
3. **Inherited narrowness is subtracted, cut-created narrowness is not.** The same opening is run on the
   plate footprint; the flat's lost area that lies inside the plate's own lost area is the footprint's
   acute tip or slot and no cut can remove it. What remains is the cut's. **`C10` fails on the remainder
   above `0.10 m²`** — a tolerance set at the float-noise floor measured above, and for no other reason.
4. **The sheet prints an area, like `C4`.** `C10` shows `x.xx m²` of flat narrower than 2.00 m, so the
   number can be read as a violation instead of as a ceiling. `C6` and `C11` are untouched.
5. **The cutter must satisfy it, not be excused from it.** `_plate_score` carries the created-pinch area
   as a term to minimise and `_fully_ok` gates on the new `C10`, which is what finally lets the existing
   `_donate_the_neck` / `_delobe_and_donate` machinery run on the plates that need it — today it is
   almost never reached, because the old `C10` never failed.
6. **Sheets the owner has read are frozen.** The five `TEST_0*_nocore_2026-09-03.html` sheets were read by
   the owner and are archived, not overwritten (`D-EU-85`); the rebuild takes a fresh build tag.

🔴 **`D-EU-88` — the rules are applied to whole neighbourhoods, seen in the 3D viewer, before any simulation.**
Ruled 2026-09-03 on the owner's own sentences: *"so what i want to apply our rules to the neighbourhoods …
before simulations i just want to see the .html 3d plans if they are working correctly … now it is time to test
with this PLANS_ES-MAD-BERRUGUETE.html, if i like we can do for all. lets go"* · *"you know that our aim to
apply floor division at least 95% of all residential builidngs. lets go"* · *"i want this format of
visualizaiton document outputs_3D/eu_ES-MAD-BERRUGUETE_viewer.html without energy demand presentation, that
means the difference between tehse plans3D will be energy demand representation compared to these outputs_3D"*
· *"seeing 3d model of the neighbourhood and click on the building seeing the pop-up window to visualize floor
division like this TEST_01_three_per_group_nocore_2026-09-03.html lets go lets go to the end"* · *"ok no need
from me about any approval, continue continue to the end"*.

1. **Every census building of a district is cut** by the no-core cutter (`build_flats`, `07_nocore_tests.py`) at
   its own flats-per-floor count `k = max(1, round(dwellings_total / storeys))`, exactly as `load_universe`
   computes it. No selection, no sample. The 95 % denominator is the district's census rows (Madrid 961; fleet
   2,544, bar 2,417).
2. **`k > 12` refuses by design** (`D-EU-65`), drawn as footprint only and counted as not covered. An unusable
   footprint or a raising cut is drawn as such and counted. Nothing is tuned to lift the count.
3. **Manifest buildings with no census row** (the IDF-writing demotions, Madrid 233) appear in the scene in grey,
   outside the denominator, on their own footer line — the separate defect of §7, never a morphology failure.
4. **The page is the `outputs_3D` viewer without energy**: 3D massing at `storeys × 3.0 m`, coloured by verdict
   (`PASS` / `FAIL` / refused / no census row / unusable or error), hover, click → modal. **The modal is the
   TEST-sheet card** — `drawplan` + the seven chips + captions, the frozen CSS — the same plan on every storey.
   Not one EUI, kWh or run id on the page. `plans3D/` = geometry; `outputs_3D/` = energy, later.
5. **Dated filenames, never a rewrite** (`D-EU-85`): `plans3D/PLANS_<district>_nocore_<tag>.html` +
   `EU-21/district_plans/<district>_nocore_<tag>.json`; the page footer prints the cutter's sha256 and
   `MAX_FLAT_ASPECT`, so a page built before the compactness repair is distinguishable from one built after.
   The old `PLANS_<district>.html` and `eu_<district>_viewer.html` stay untouched.
6. **Madrid first, then the other three in the same run**; the owner's fifth sentence lifts the reading gate.
   `D-EU-55` is not lifted by it: no simulation.

Plan: `implementation/PLAN_eu21-district-viewer-2026-09-03.md`. Only file written: `scripts/eu21/08_district_viewer.py`.

🔴 **`D-EU-89` — the district run is audited; the residual is not excused, the pop-up takes the EU-11 modal, the archive is authorised.**
Ruled 2026-09-03 evening on the director's audit of both executors and on the owner's three sentences of the
afternoon: *"you can archive non core versions"* · *"what kind of a visualizaiton is taht, look how it was beautiful before"* (with a screenshot of the EU-11 viewer's pop-up: dark modal, one colour per flat labelled D1…Dk, storey buttons, north arrow, scale bar, zone table) · *"i want this style of pop-up windows to see floor plans, assigned"*.

1. **The pop-up is the EU-11 modal, not the TEST-sheet card** (`D-EU-88` clause 4 amended). The `openPopup` /
   `drawFloorPlan` pair of `scripts/generate_eu_3d_viewers.py` **at commit `3fef4e33`** (`:382`, `:469`, zone
   table `:535`, `ZONE_COLORS` `:376`, modal CSS `:76–97`, canvas `:153`), fed with the no-core flats: the
   footprint outline, one colour per flat with `D1…Dk` labels, north arrow, scale bar, storey buttons that
   all show the same plate (`D-EU-79`), the zone table `Zone Name / Colour / Dwelling Index / Storey
   Elevation`. Under the drawing: the verdict badge and the seven check chips with the TEST sheet's printed
   values. No archetype, no EUI, no simulation provenance — those lines are what `outputs_3D` adds later.
2. **The residual is not excused and no rung is chosen yet** (`FINDING 242`). `D-EU-86` clauses 1–2 stand:
   `MAX_FLAT_ASPECT` is not frozen; a second repair round (`T05d`) attacks the ring/wing family and the
   `MultiPolygon` fault first. If `FAIL 0` is still unreachable after it, the constant is set to the
   **strictest** rung, 2.5, and every residual plate is delivered as an honest `FAIL` — never the loosest
   rung, because choosing the rung that fails least is the loosening `D-EU-86` forbids.
3. **The 17 raising buildings are a cutter defect** (`FINDING 243`), fixed in `T05d`, never a footprint
   excuse. From now on the four district JSONs are an acceptance input beside the five sheets: every census
   building ends `direct` or `REFUSED_K_GT_12`, never `ERROR`.
4. **The district pages are rebuilt twice, never overwritten**: `_r2` now (pop-up restyled per clause 1, the
   cutter of the moment printed as *not frozen*), `_r3` once the compactness plan closes. The
   `_2026-09-03` pages stay as the owner read them.
5. **The archive is authorised once.** *"you can archive non core versions"* lets `T07` move the owner-read
   `TEST_0*_nocore_2026-09-03.html` set and the `*_nocore_2026-09-02` rules docs into `archive/` after `T06`
   has delivered their replacements — one pass, with the citation sweep, not before `T06`.
6. **`D-EU-55` untouched**: no simulation.

The audit itself, for the record: Madrid 961 census / 946 direct / 871 PASS / 7 refused (`k` 15–31) / 8 error /
233 generic fallback; Lyon 297 / 293 / 277 / 3 / 1 / 233; London 82 / 69 / 53 / 13 (`k` 17–34) / 0 / 1,159;
Bologna 1,204 / 1,197 / 1,034 / 0 / 7 / 16. Fleet: 2,505 of 2,544 drawn (98.5 %, bar 2,417), **2,235 PASS all
seven (87.9 %)** — clearing the 95 % target on drawn plates by 88 buildings. Total structures with interior floor
plans across all four districts: **4,146 of 4,186 (99.0 %)**. Every direct record carries all seven checks; `kwh` / `eui` /
`energy` appear 0 times on the four pages; the five owner-read sheets are byte-identical to
`archive/reviewed_2026-09-03/`; the `_r2` sheets and district viewers exist. One text error corrected here: `D-EU-87`
named plates 30127 and 28754 `COMPLEX_MULTI_WING`; both are `COURTYARD` in every JSON.

🔴 **`D-EU-90` — generic fallback for uncatalogued buildings, dark green styling, and baseline preservation.**
Ruled 2026-09-03 on the owner's instructions (*"we can lable them as unknown, and maybe we can generate generic floor plans for these beuildings based on theire groups... color them as dark green... apply generic floor division for all others... for the rest can you put in the archive in order to preserve the previous files as well"*).

1. **Rules Document Chapter:** Added `<section class="block" id="generic_fallback">` titled *"Generic Floor Plans for Uncatalogued Buildings (No-Census Fallback)"* into `rules/RULES_dwelling_layout_groups_nocore_2026-09-02.html` (now `rules/archive/RULES_dwelling_layout_groups_nocore_2026-09-02.html`; the chapter is carried unchanged into the live `rules/RULES_dwelling_layout_groups_nocore_2026-09-03.html`, T07 of `PLAN_eu21-compactness-2026-09-03.md`). Uncatalogued manifest buildings outside the census are classified into the EU-11 morphology taxonomy via `M20._measure_footprint` + `cls`, assigned estimated dwellings per floor ($k = 1$ for `SLIVER`, $k = \max(1, \min(12, \text{round}(\text{area} / 70.0)))$ for others), partitioned with `build_flats`, and styled dark green (`rgb(24, 94, 46)`).
2. **Fleet Rollout Across All 4 Districts:** Implemented via `--generic-no-census` in `scripts/eu21/08_district_viewer.py` and built into the active `_r2.html` viewers:
   - Madrid (`ES-MAD-BERRUGUETE`): 233 generic fallback buildings (1.05 MB)
   - Lyon (`FR-LYO-HAUTCOEURPENTES`): 233 generic fallback buildings (0.50 MB)
   - London (`GB-LDN-STDUNSTANS`): 1,159 generic fallback buildings (0.70 MB)
   - Bologna (`IT-BOL-GALVANI2`): 16 generic fallback buildings (1.22 MB)
   - **Fleet Total:** **1,641 uncatalogued buildings** fully partitioned into dwellings; **0** unpartitioned massings remain in the 4 districts.
3. **Interactive Modal:** Generic buildings carry the badge `GENERIC (NO CENSUS)`, dwelling count subtitle, interactive multi-storey switching (`F0`, `F1`, etc.), planar labels `D1`..`Dk`, North arrow, scale bar, and 4-column zone table (`Zone Name`, `Colour`, `Dwelling Index`, `Storey Elevation`) with hover highlighting.
4. **Baseline Archiving:** The previous baseline non-r2 files (`PLANS_*_nocore_2026-09-03.html`) are preserved in `docs/docs_ACTIVE/europeanLocations/plans3D/archive/`. Active interactive viewers remain as `*_nocore_2026-09-03_r2.html`. `plans3D/index.html` links directly to active `_r2` viewers and references the archive.
5. **Audit Verification:** All 4 active `_r2` pages pass all gates: 0 forbidden terms (`kwh|eui|energy|archetype`), 0 `srcdoc`, 1 `Dwelling Index`, 1 `.chk{`.

---

🔴 **`D-EU-91` — the simulation gate is 95 % PASS in one neighbourhood, and it is read on PASS, never on drawn.**
Ruled 2026-09-03 on the owner's own sentences, given while leaving the session: *"if you reach 95% floor division
any of the neighbourhood, start simulations, lets go"* and *"no need to ask me, aim is the reach 95% for floor
dicison, and then simualtions"*.

1. **This is the `D-EU-55` authorisation, and it is conditional.** `D-EU-55` bars any EnergyPlus run without the
   owner's own sentence. That sentence now exists, but it is a *conditional* one: the campaign starts **when, and
   only when, one of the four districts reaches ≥ 95 % of its census plates passing all seven checks**. Until a
   district clears that bar, `D-EU-55` still bars the run. No partial credit, no fleet average, no "close enough".
2. **The denominator is the district's census plates; the numerator is `verdict == "PASS"`.** "Floor division" is
   the plate being *correctly divided*, which is what the seven checks measure. It is **not** `drawn`: drawn reads
   99.1 % fleet-wide already and has read above 95 % since `_r2`, so reading the gate on drawn would make the
   owner's condition vacuous on the day it was written — it plainly was not meant to be. `_r3` reads Madrid
   **83.6 %** · Lyon **83.2 %** · London **61.0 %** · Bologna **75.7 %**. The gate is open, not met.
3. **What "start simulations" does not license.** It authorises the run, not a claim about its output. Every
   standing caveat survives it — `FINDING 201` (the EU-11 district EUIs carry a +11.2 % zone over-count and are
   not validated district EUIs), the 939-building IDF-writer demotion, `FINDING 204`, and the heating-only scope.
   A number produced under this ruling is quotable only with those caveats attached.
4. **No executor may start a run on this ruling.** The gate is evaluated by the director against this clause and
   `CHECKLIST_european_locations_v5.md`; a plan's executor stops at its last checkpoint and reports.

🔴 **`D-EU-92` — the `k > 12` refusal is demoted from a ceiling to an attempt; `k` itself is still untouchable.**
Ruled 2026-09-03 on the owner's sentence *"about orange continue as you progress … to solve as much as orange
buildings, lets go"*, answering the director's question of whether `k` may be clamped.

1. **What changes.** `08_district_viewer.py:165-169` refuses every plate with `k > 12` **before the cutter is
   called**, so no evidence has ever existed that these 23 plates cannot be cut — `D-EU-65` declared a ceiling and
   never measured one. The refusal becomes an attempt: cut at the declared `k`, run the seven checks, and refuse
   only what fails them.
2. **What does not change.** `k` is still exactly what `load_universe` computes (`D-EU-88` clause 1) — not
   clamped (orange Tier 1), not redistributed across storeys (orange Tier 3, red Diagnosis 4). The seven checks
   keep their thresholds; `MAX_FLAT_ASPECT` stays 2.5. A plate turns green only by passing the same checks as
   every other plate, which makes this the **opposite** of the exemption `D-EU-84`/`D-EU-86` forbid.
3. **Failure is a result.** A `k > 12` plate that fails the checks stays refused, with its `fail_by_check`
   recorded so the residual is inspectable. No plate may be named individually in code (`D-EU-86`).
4. **Executed by** `implementation/PLAN_eu21-colour-repair-2026-09-03.md` `T05`.

🔴 **`D-EU-93` — `C11` does not apply to an undivided plate (`k = 1`).**
Ruled 2026-09-03 by the owner, in their own words *"yes lets go, i say yes D-EU-93, lets go"*, answering the
director's question **"should `C11` apply at `k = 1`?"** (recommendation: no). This is the ruling `FINDING 245`
declared to be the owner's alone.

1. **What changes.** At `k = 1` the single flat **is** the plate: its aspect is the footprint's aspect, handed to
   the cutter by the census and the building outline. `C11` (`D-EU-82`) exists to stop a *cut* producing a ribbon;
   with no cut made there is nothing for it to judge, and no partition of any kind could change the number. The
   check is therefore not evaluated when `len(live) <= 1`. The measured aspect is still computed and still shown
   on the plate card, marked `(k=1, D-EU-93)` — it is reported, not judged.
2. **What does not change.** `MAX_FLAT_ASPECT` stays **2.5** and is never moved (`D-EU-89` clause 2 and the
   standing refusal of every proposal to loosen it). At `k >= 2` `C11` applies exactly as before — the 75 plates
   failing `C11` only at `k > 1` stay red, and that is the intended outcome. No other check, threshold, or file
   changes; no plate is named in code (`D-EU-86`); no exemption list exists (`D-EU-84`).
3. **Why this is not the exemption `D-EU-84`/`D-EU-86` forbid.** Those forbid excusing a plate *from a check it
   fails*. This ruling states that the check has **no subject** at `k = 1` — a scope statement about `C11`, applied
   uniformly to every undivided plate in the fleet, decided by the geometry and not by which buildings would
   benefit. The distinction was put to the owner in exactly these terms before the ruling was given.
4. **Executed by** `implementation/PLAN_eu21-colour-repair-2026-09-03.md` `T07`, rebuild tag `2026-09-03_r5`.
   Projected before the build from the `_r4` JSONs: **+175 PASS** (Madrid +49, Lyon +17, London +6, Bologna +103)
   of the 187 `C11`-at-`k=1` failures; the other 12 also fail `C4`/`C5` and stay red. `FINDING 245`'s per-district
   ceilings (Madrid 94.8 · Lyon 94.3 · London 92.7 · Bologna 90.5 %) were computed **with** `C11` at `k = 1` and
   are lifted by this ruling; they are not withdrawn, they no longer bind.

🔴 **`D-EU-94` — the simulation gate is armed, conditional on 95 %, and it is Speed.**
Ruled 2026-09-03 by the owner, in their own words *"ok once we reach 95, we will immediately start simulation on
the speed cluster cloud computing"*. This is the owner's own sentence for the purposes of `D-EU-55`, and it
supersedes `D-EU-91`'s vaguer conditional by naming the machine.

1. **What it authorises.** An EnergyPlus campaign on the Speed cluster, and nothing before the 95 % floor-division
   condition is met on measured `PASS` over `census_rows`. It is an *arming*, not a start order: the condition is
   read from the district JSONs, never asserted.
2. **Which 95 %.** `D-EU-91`'s reading is unchanged — **any** one neighbourhood crossing 95 % opens the gate; the
   fleet number does not have to cross. Read on `PASS`, never on `drawn` (`D-EU-90`).
3. 🔴 **The gate is not the only blocker, and this ruling does not clear the other one.** The IDF-producing engine
   `openubem/geometry/european_residential.py` is still **core-era** — 2,920 lines, 116 × "core", 26 × "corridor",
   **0** occurrences of "nocore", "C11" or "MAX_FLAT_ASPECT". A run launched today would simulate core-and-corridor
   layouts, **not** the no-core plans the seven checks proved. The no-core rules must be carried into that engine
   before any submission, or the campaign measures the wrong building stock. This is stated as a fact of the code,
   not as a refusal of the order.
4. **`D-EU-54` still stands.** The owner reads `plans3D/` and confirms; that gate is separate from this one and is
   not consumed by this sentence.
5. **Cluster rules apply unchanged.** `sbatch --array` only, never the login node, `--time=7-00:00:00` minimum
   (`CLAUDE.md` §CLUSTER). Fire-and-forget, then read the output file.

🔴 **`D-EU-95` — the engine carry-in is an extraction, and its acceptance test is bit-parity with `_r5`.**
Ruled 2026-09-03 by the director, on the owner's *"lets go, to the end, no more ask, when you are satisfied,
start simulations"*. `D-EU-94` clause 3 named the engine as the remaining blocker; this rules **how** it is closed.

1. **Extraction, never re-implementation.** The proven cutter moves into
   `openubem/geometry/european_nocore.py` as **copied source** — body for body, comment for comment, constant for
   constant — from `scripts/eu21/07_nocore_tests.py` (sha256 `fe75c96e…`, the recorded provenance of all four
   `_r5` JSONs). It is not re-derived, tidied, refactored, optimised or improved on the way. **Any behavioural
   difference from `_r5`, however small and however defensible, is a defect, not an improvement** — because
   `D-EU-54` had the owner review *those* plans, not plans that resemble them.
2. **The gate is bit-parity, and it is two-sided.** For all 2,544 census plates the engine must reproduce `_r5`'s
   verdict, flat count, all seven check strings and the flat geometry to `1e-6 m²`. The engine may not **pass** a
   plate `_r5` failed any more than it may fail one `_r5` passed. Measured by `scripts/eu21/09_engine_parity.py`;
   **0 mismatches or the plan does not continue.**
3. **The corridor path is parked, not deleted.** `generate_european_ruled_storey_layout`, the group schemes,
   `generate_external_unconditioned_core` and every circulation constant stay in the file, reachable through an
   explicit `EUROPEAN_LAYOUT_REGIME = "ruled"`. `D-EU-79` parked that path with its files intact; a carry-in does
   not get to retire it.
4. **A failing plate falls back honestly.** A storey the seven checks refuse returns
   `dwelling_layout_emitted=False` and the building takes the existing `one_zone_per_floor` massing box — exactly
   as any other unlayoutable building does today. No failing partition is ever emitted, repaired at the seam, or
   relabelled.
5. **`07_nocore_tests.py` is never edited.** Its sha is the provenance of the delivered build. Read it, copy from
   it, never write to it. Executed by `implementation/PLAN_eu-engine-nocore-carryin-2026-09-03.md`.

**`D-EU-96` — the 95 % coverage bar is retired** (owner 2026-09-03, verbatim: *"this will be last trial, and if
we can not reach 95% for every neighbourhood, no worries, this level is enough itself, i beleive we can start
simulations when the agent finish its job"*). The `_r5` levels are accepted as delivered — Madrid **95.3 %** ·
Lyon **94.6 %** · Bologna **90.1 %** · London **86.6 %**, fleet **92.5 %** (2,353 of 2,544). No further
colour-repair trial is ordered, and the three districts below 95 % stop being a blocker. Three things the
ruling does **not** do:

1. It does not move `MAX_FLAT_ASPECT`. Still **2.5**, still barred from moving (`D-EU-84`, `D-EU-86`), and
   nothing here was obtained by loosening a check.
2. It does not waive `CP-2`. The owner's *"when the agent finish its job"* names that gate; the IDF rebuild
   must still show zero `*_circulation` zones and a route count matching `T05a`'s `EMITTED` (`FINDING 246`).
3. It does not consume `D-EU-54` — the owner reading `plans3D/` and confirming is a separate, still-open gate.

**`D-EU-97` — the 107 low-density buildings stay in, flagged, not excluded** (owner 2026-09-03, verbatim:
*"so i beleive these buildings look not residential, are we sure that they are residential. ok ok. no need to
trying to include as many buildigns in the system, lets keep it that way"*). Taken on `FINDING 248`. The
ruling:

1. **No exclusion filter is added** — not to the cutter, not to `morphology_census.csv`, not to the EU-02
   manifest. The universe stays exactly as delivered: 2,544 census buildings, 2,529 drawn, 2,353 `PASS`.
2. **No effort is spent widening coverage.** The owner's *"no need to trying to include as many buildings"*
   closes the question the same way `D-EU-96` closed the 95 % bar. Nothing further is attempted on the
   145 residual failures.
3. **The 107 are recorded, not silently simulated as sound.** They carry > 500 m² of gross floor area per
   declared dwelling (Madrid 50 · Bologna 47 · London 8 · Lyon 2; `IT-BOL-GALVANI2/30090` at 4,382 m²/dwelling)
   and are almost certainly non-residential or mis-tagged in OSM. `FINDING 248` is the record. **Never quote a
   per-dwelling or per-area result for these buildings as a residential figure**, and never present the fleet
   EUI without noting that 4.2 % of the stock is of unverified use.
4. It changes nothing else — `MAX_FLAT_ASPECT` stays 2.5, `CP-2` still gates the submission, `D-EU-54` stays
   open.

**`D-EU-98` — the director builds and submits the Speed campaign unattended** (owner 2026-09-03, verbatim:
*"ok lets do it that way, it looks like it will take some time, so what is my suggestion is that you continue
to build and submit simulations, i will sleep, i can not wait, and once you submit the tasks update the prompt
of manager. thank you."*). This is the owner's own sentence, given in reply to the sequence they were told —
Bologna finishes → `CP-2` audit → clean → submit. The ruling:

1. **`T06` passes to this session.** §6 T06's "director only, after `CP-2`" is satisfied: the director both
   audits and submits, with no further check-in. The owner is asleep and is not to be woken for anything short
   of a blocker.
2. **`CP-2` is not waived.** The owner said *"lets do it that way"* to the stated order, in which the audit
   comes first. The rebuilt IDFs must show **zero `*_circulation` zones** and route counts reconciled against
   `T05a`'s 2,279 `EMITTED` (`FINDING 246`) before a single `sbatch` is issued. A `CP-2` failure stops the
   submission and is reported, not worked around.
3. **The cluster rules are unchanged and absolute.** No compute on the login node — `sbatch --array`,
   fire-and-forget, then read the output file. `--time=7-00:00:00` minimum on every submission, on the CLI,
   never baked into the shared `.sbatch`. Remote shell is tcsh; every command goes through the `_ssh()` helper
   (`scripts/cluster/t08_harvest_results.py:104`). Confirm `squeue -u o_iseri` is clear of this arc's jobs
   before submitting, and never touch another project's runs.
4. **The prompt is updated after submission, not before** — the owner's *"once you submit the tasks update the
   prompt of manager"*. `prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` records the `CP-2`
   outcome, what was shipped, the job ids, and where the results will land, so the owner's fresh session
   resumes at the harvest.
5. It changes nothing else — `MAX_FLAT_ASPECT` stays 2.5, `D-EU-97`'s "unverified use" caveat rides with every
   figure the campaign produces, and `D-EU-54` stays open: the owner has still not read `plans3D/` and
   confirmed, and no result may be presented as validated layout until they do.

**`D-EU-99` — root-cause `FINDING 249` before any campaign** (owner 2026-09-04, verbatim: *"ok then prepare
investigation plan to solve 5th gate for CP-2, and then start execution"*), taken on the director's own
recommendation in reply to `D-EU-99` being raised as the one open decision after `CP-2` failed. The ruling:

1. **A dedicated investigation plan is authorised** — `PLAN_eu-nocore-interzone-rootcause-2026-09-04.md` —
   scoped to root-causing and, if confirmed, remedying `FINDING 249`'s fifth `CP-2` gate. It does not reopen
   `CP-1` and does not touch the accepted `_r5` cutter (`D-EU-95`).
2. **Speed submission is pre-authorised, contingent on `CP-2` re-passing** (owner, same message, verbatim:
   *"i want to handle this one and submit the simulations on the speed, we are close to 95% for each
   neighbourhood, in Madrid we already pass 95% threshold, we are ready to go, solve this last pass of CP-2,
   and start simulations"*). The 95 % coverage bar is a different, already-cleared gate (`D-EU-91`/`D-EU-96`);
   the only remaining blocker is `CP-2`'s fifth gate. Mirrors `D-EU-98`'s pattern: the director builds and
   submits once `CP-2` is signed clean, no further check-in required, cluster hard rules unchanged (`sbatch
   --array` only, `--time=7-00:00:00` minimum, `_ssh()` helper, never the login node). `CP-2` is **not**
   waived by this authorisation — a failed re-audit still stops the submission and is reported, not worked
   around.
3. **New working hypothesis, not yet confirmed at ruling time**: `generate_european_building_dwelling_layout`
   caches one independent `cut_storey_nocore` cut per distinct per-floor dwelling count
   (`openubem/geometry/european_residential.py:2664-2684`) and groups only *consecutive equal-count* floors
   into one `EuropeanStoreyGroup`; a building whose per-floor dwelling count changes gets two structurally
   unrelated partitions of the same footprint at that transition, which is exactly the class of divergent
   ceiling/floor ring `intersect_match` is documented (`FINDING 210` root-cause pass) to resolve inconsistently.
   The two probes already run for `FINDING 249` tested footprint-level stats, never per-floor count variation —
   this is untested ground, not a re-check of a closed question.
4. **Investigate first, implement only after the director confirms the mechanism** — a `CP-1` checkpoint sits
   between characterization and any code change, per this plan's own hard rules.
5. Nothing else changes: `openubem/idf/surfaces.py` stays non-editable (`D-EU-41`), `MAX_FLAT_ASPECT` stays 2.5,
   `D-EU-54` stays open.

**`D-EU-100` — `CP-2` re-sign-before-campaign gate lifted** (owner 2026-09-04, verbatim across three messages:
*"for that reason use speed cluster in parallel, LISTEN TO ME"*; *"delete taht rule, no more need that rule,
we already handled floor divisions, lets go"*; *"delete this one ... delete this one"*, referring to `D-EU-99`
clause 2's "Speed submission ... contingent on `CP-2` re-passing"). The ruling: clause 2 of `D-EU-99` is
superseded — the director may build and submit the full `T06` Speed campaign without waiting for `T04`'s
local `CP-2` gate-5 re-audit to finish or pass first. `T03`'s 16-building EnergyPlus regression check had
already completed clean (16/16 `.err` outputs present, `openubem/outputs/eu_evidence/EU-21/
finding249_remedy_validation/t03_energyplus/`) at the time of this ruling; those raw results were not yet
read for Fatal/Severe counts before this decision was taken — that is the director's own gap, not the
owner's. Everything else `D-EU-99` set is unchanged: no `_r5` cutter edits (`D-EU-95`), no
`openubem/idf/surfaces.py` edits (`D-EU-41`), cluster hard rules unchanged (`sbatch --array` only,
`--time=7-00:00:00` minimum, `_ssh()` helper, never the login node, `D-EU-98`'s unattended-submit pattern).

**`D-EU-106` — repaint the `outputs_3D` floor-plan modal in the `plans3D` visual style** (owner 2026-09-07,
verbatim: *"floor plan visual style is different, i want to apply same style of this plan view
[`plans3D/PLANS_ES-MAD-BERRUGUETE_nocore_2026-09-03_r5.html`] for the outputs
[`outputs_3D/eu_ES-MAD-BERRUGUETE_viewer.html`]"*,
`implementation/DONE/PLAN_eu-viewer-planstyle-2026-09-07.md:18`). Presentational only — no polygon, zone
payload, join, or data-source change; scoped to `scripts/generate_eu_3d_viewers.py`'s CSS block, modal
markup and `drawFloorPlan`; `08_district_viewer.py` and every `plans3D/PLANS_*.html` stay read-only style
references, never edited or re-run. **Complete 2026-09-07** — T01-T05 all done, four viewers regenerated
and mirrored, primary/mirror `sha256` matched (`PLAN_eu-viewer-planstyle-2026-09-07.md:167-243`).

**`D-EU-107` — balance the dwelling cut; re-plan and re-simulate only the affected buildings** (owner
2026-09-07, verbatim: *"based on the global rules […] we are aiming homogeneous floor planning, but there
are some flaws […] please scan similar buildings, re-plan floor plans and re-simulate"*,
`implementation/PLAN_eu-plan-homogeneity-2026-09-07.md:15-17`). Scopes, does not supersede, `D-EU-105`'s
"per affected building only" clause: the affected set is measured, not assumed, at **344 plates fleet-wide**
(`CP-1` SIGNED, T01), of which 340 sit in the simulated ceiling82 population. Sub-rulings:

1. **`D-EU-107 f`** (`:182-230`) — corrects the T02a spec's `_plate_score` ranking tuple to booleanise `C10`
   ahead of the new `spread` term, after the uncorrected order flipped 458 `PASS`→`FAIL` verdicts on `C10`
   alone. Corrected order recovers **275 of 344 to `spread >= 0.50`, 69 residual**, **0 regressions** on all
   seven checks (`CP-2` SIGNED, `:292-318`).
2. **`D-EU-107 g`** (`:334-365`) — re-points the engine-parity gate at a freshly regenerated
   `2026-09-07_r6` baseline, after the plan's own bench change invalidated the 2026-09-03 `_r5` reference as
   a same-day comparator. Both runs land exactly as predicted: `--baseline-tag 2026-09-07_r6` → `0/0/0/0`
   over 2,529 plates; `--baseline-tag 2026-09-03_r5` → `0/0/1,101/32`, matching T03's pre-correction numbers
   (`CP-3` parity half SIGNED, `:598-621`).

`CP-3`'s hash half is **UNSIGNED**, pending `D-EU-109`'s merged `T03m` re-emission (`:621`). T04
(re-emit affected IDFs) not started. T05-T07 (Speed campaign, harvest, republish) are director-only and fold
into `D-EU-109 e`'s single merged wave.

**`D-EU-108` — London: why so few buildings are simulated, and how many more can be** (owner 2026-09-07,
verbatim: *"most of the buildings are not simulated why, it looks like even similar buildings some
simulated some excluded […] i think there could be more buildings to simulate"*,
`implementation/PLAN_eu-london-coverage-2026-09-07.md:11`). T01 closed `FINDING 259` (the viewer read the
wrong tree) — `CP-1` SIGNED (`:172-183`). T04's decision request
(`debugs/docs/DECISION_REQUEST_D-EU-108_london_recovery_2026-09-07.md`) was **ruled 2026-09-07, owner
verbatim "yes, admit 2 and 3" / "lets go"** (`PLAN_eu-london-coverage-2026-09-07.md:215`): **Option 2**
(terrace-row age inheritance — inferred, not observed, provenance `INFERRED_TERRACE_NEIGHBOUR_AGE`) and
**Option 3** (storey recovery) admitted; Option 1 moot (already in production, 0 recoverable); Option 4
declined. Target London **451 -> 758 of 1,242 (36.3 % -> 61.0 %)**, of which 307 rows are inferred.
`D-EU-108 f` (straddle disambiguation, `:414-443`) completed 2026-09-07 — `CP-4` SIGNED: **London
706/1,242**, hash control **412/412** over the 39-building `FINDING 263`-excluded population (`:585-587`).
The owner then separately instructed (verbatim *"start, building and simulations, lets go"*, `:588-591`) an
**unfolded, London-only Speed campaign** for the 255 net-new buildings only — **submitted 2026-09-07, job
`1310803`** (`:588-608`), explicitly **provisional**: emitted by the pre-`D-EU-109`/`D-EU-107` engine, 9 of
255 already carry the discard defect, and the T07 restatement must be redone after the merged wave lands
(`:613-621`). It does not supersede or fold into the merged wave's own scope. `D-EU-108` complete through
T05b; T06/T07 (harvest, final restatement) fold into `D-EU-109`'s merged wave.

**`D-EU-109` — recover the discarded dwelling divisions: 1,524 simulated buildings carry no floor
division** (owner 2026-09-07, verbatim: *"even i am seeing these buildings under the EUI visualisation but
they do not have floor division, this is absurd. witout floor division no simualtion"*; authorisation
verbatim: *"go ahead, execute this plan too"*,
`implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md:9-14`). Authorised end to end, including
the merged re-emission (`D-EU-109 e`), the single Speed campaign (T06) and the EUI restatement (T07);
director signs `CP-1`-`CP-3` on the plan's own measured gates, owner returned to only on a gate failure.
Sub-rulings (`:214-249`): **a** — the remedy is vertex *removal*, not snapping; **b** — cleanup runs at two
points (pre-cut footprint ring, post-cut zone rings); **c** — removal criterion is the detector's own
unchanged math (`NEAR_DUPLICATE_VERTEX_TOLERANCE_M`, `COLLINEAR_VERTEX_ANGLE_TOLERANCE_DEG`), iterative to
a fixed point; **d** — every district EUI is restated, not assumed, at T07; **e** — one merged re-emission
and one Speed campaign covers `D-EU-107` + `D-EU-108` + `D-EU-109` together, this plan's engine change
lands first. **`D-EU-109 f`** (`:477-512`) — after `CP-2` held the initial `1e-6` relative-area budget as
self-defeating (measured 500x too tight to admit the flagged vertices), the final removal criterion is:
perpendicular distance to chord `<= 0.010 m` **and** per-removal relative area change `<= 1e-3` **and**
cumulative relative area change per ring `<= 2e-3`, chosen from T02b's measured distributions (171/173
undivided buildings recoverable). **`D-EU-109 g` / T03m** (`:329-356`) — merges this plan's T03,
`D-EU-107`'s T04 and `D-EU-108`'s re-emission into **one** pass over each district's final population
(ceiling82 for `ES-MAD`/`FR-LYO`/`IT-BOL`, the 706-building `GB-LDN-STDUNSTANS_recovery_2026-09-07/` set for
London), output to new `<DISTRICT>_final_2026-09-07/` trees; `*_ceiling82_2026-09-05/` trees are never
written to. `CP-1` SIGNED (`:406-417`); `CP-2` HELD then superseded by `D-EU-109 f` (`:429-460`). **T03m is
in execution as of 2026-09-07** (still running for `ES-MAD` and `IT-BOL`); T06 (merged Speed campaign) has
not yet been submitted.


🔴 **`D-EU-110` — `D-EU-84` is CLOSED as an accepted named residual; `MAX_FLAT_ASPECT` stays 2.5 and
still may not move.** Ruled by the owner 2026-09-08, on the 4J pre-registration's freeze condition 2
(`messages_GSSCanada/2026-09-08_4J_to_OpenUBEM_layout_payload_and_two_questions.md`). The ladder of
`D-EU-84` was run over all 550 plates and no rung reached `FAIL 0` after two genuine repair rounds
(`FINDING 242`); per `D-EU-89` clause 2 the constant sits at the strictest rung, **2.5**. The ruling:

1. **`D-EU-84` is closed, not open work.** The calibration it demanded was performed and reported; its
   outcome is that no calibrated `FAIL 0` value exists for this plate population. That outcome is the
   answer, and it is accepted as such.
2. **The residual is named, counted and carried, never hidden:** **81 of 550 plates** ship an honest
   `FAIL` on the aspect check, across **57 unique buildings** — thick-band courtyard rings and dense
   `n = 12` multi-wing plates whose wings do not separate under `lobes_of`. Any quotation of the flat
   division must carry that count.
3. **`EU-21` acceptance criterion 3 (§5) is satisfied by this ruling as a declared residual.**
   Criterion 2 (`FAIL 0` on 550 plates) remains **not met** and is not closed by this ruling.
4. **The threshold is still frozen against accommodation.** `MAX_FLAT_ASPECT` may not be moved to make
   any downstream consumer's condition pass — `D-EU-84`'s and `D-EU-86`'s bar on exemptions,
   carve-outs and loosened rungs survives its own closure.
5. **`D-EU-87` is implemented** — `C10` was rebuilt as a created-pinch test (`FINDING 241`); fleet
   created-pinch fell 1358.78 → 134.63 m² (−90 %).

---

## 5. Acceptance

**`EU-21` is done** when all four hold:

1. The eleven-group rules document states, per group, how the plate is read and how the flats are cut —
   in bullet form, checkable against the drawn plate.
2. The five test sheets grade **550 plates** with **`FAIL 0` on all seven checks**, no plate refused,
   no plate dropped, no threshold moved.
3. `MAX_FLAT_ASPECT` is fixed at one calibrated value with the ladder recorded (`D-EU-84`) — **satisfied
   2026-09-08 by `D-EU-110` (§4) as a declared residual**: the ladder was run, no rung reached `FAIL 0`,
   the constant is frozen at 2.5 and 81/550 plates over 57 buildings ship a named `FAIL`.
4. The director has re-derived the verdicts **from the stored polygons**, not from the sheets' own
   verdict strings.

**`EU-17`/`EU-18` are done** when, measured on the emitted IDFs: ruled coverage ≥ 95 % in each district
with the residual listed by named reason; `FINDING 213` → 0; the parity gate exits 0; dwelling and area
conservation hold; `FINDING 214`'s denominator question is settled in writing. **None of this is
reachable until `EU-21`'s rules are carried into `openubem/geometry/european_residential.py`** — a step
that is **identified and not ordered**.

**`EU-19` has two gates, both owner-held and neither inferable from silence:** the owner reads the
`plans3D/` pages and confirms (`D-EU-54`), and the owner authorises the run in their own sentence
(`D-EU-55`).

### Gates that need the owner, specifically

Compact index, current as of 2026-09-04; full rulings and quotes are in §4 by decision number,
never repeated here.

- 🔴 **`D-EU-54` — read `plans3D/` and confirm.** Comes *after* the engine carry-in, not before. Open.
- ✅ **`D-EU-91`/`D-EU-94` — simulation permission, conditional on ≥ 95 % `PASS` in any one district.**
  Met: Madrid 95.3 % (916/961). Meeting it does **not** clear the engine blocker (`D-EU-94` clause 3).
- ✅ **`D-EU-93` — `C11` not evaluated at `k = 1`.** Taken, carried into `_r5`.
- ✅ **`D-EU-96` — the 95 % coverage bar is retired.** `_r5` accepted as delivered (fleet 92.5 %).
- ✅ **`D-EU-97` — the 107 low-density buildings stay in, flagged, not excluded.** `FINDING 248`.
- ✅ **`D-EU-98` — the director builds and submits the Speed campaign unattended.** `CP-2` not waived.
- 🔴 **`CP-2` (engine carry-in IDF audit) — FAILED.** `FINDING 249`, re-measured as `FINDING 250` (171 real layouts recovered, reroute rate 50.2%). Wait-for-`CP-2` gate lifted by `D-EU-100`.
- ✅ **`D-EU-99` — root-cause `FINDING 249` before any campaign.** Taken 2026-09-04; investigation plan
  authorised. Clause 2 (Speed submission contingent on `CP-2` re-passing) superseded by `D-EU-100`.
- ✅ **`D-EU-100` — `CP-2` re-sign-before-campaign gate lifted, owner's own call.** Taken 2026-09-04;
  director authorised to build and submit `T06` without waiting on `T04`'s local re-audit.
- ▶ **`T06` (Speed cluster campaign) — SUBMITTED AND RUNNING IN PARALLEL** across all 4 districts (Jobs
  1305158, 1305167, 1305176, 1305186; 2,527 tasks total, 32 active parallel tasks under `%8` throttle).
- 🔴 **Restarting the parked corridor path — owner-only** (`D-EU-79`).
- ✅ **`D-EU-37` — extend the `D-EU-04-G` typology table to recover Lyon's 176 mid-rise buildings.** Ruled
  2026-09-04, owner's own words: *"100% full"* / *"make it possible"* — option 1 taken. Implemented
  (`FINDING 255`): new bucket `2<=dwellings<=12 & 5<=storeys<=9 -> MFH` added to `derive_bdtopo_building_type`
  (`openubem/semantic/european_archetype_mapping.py:199-200`). Lyon `population_prepared` 293→469 (+176),
  `TYPOLOGY_SIGNALS_DISAGREE` 186→10 (the 8+2 out-of-scope outliers, unchanged). Fleet 2,890→3,066/4,186
  (73.2 %). Decision request ruled and archived:
  `debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-37_typology_table_extension_2026-09-04.md`.
- ✅ **`D-EU-106` — repaint the `outputs_3D` floor-plan modal in the `plans3D` visual style.** Ruled and
  completed 2026-09-07, `implementation/DONE/PLAN_eu-viewer-planstyle-2026-09-07.md`.
- ▶ **`D-EU-107` — balance the dwelling cut (`C12`), re-plan/re-simulate the affected plates only.** In
  execution as of 2026-09-07. `CP-1` (344 affected plates) and `CP-2` (0 regressions, 275/344 recovered)
  SIGNED; `CP-3` parity half SIGNED, hash half UNSIGNED pending `D-EU-109`'s `T03m`. T04-T07 not started,
  fold into `D-EU-109`'s merged wave.
- ▶ **`D-EU-108` — London coverage recovery.** In execution as of 2026-09-07. `CP-1` (`FINDING 259`
  closed), `CP-2` and `CP-4` (706/1,242, hash control 412/412 over the 39-building `FINDING 263` exclusion)
  SIGNED, complete through T05b. A separately-instructed, London-only Speed campaign for the 255 net-new
  buildings (job `1310803`) was submitted 2026-09-07 and is explicitly provisional; T07's final restatement
  folds into `D-EU-109`'s merged wave.
- ▶ **`D-EU-109` — recover the discarded dwelling divisions (1,524 undivided of 3,344 simulated,
  `FINDING 261`).** In execution as of 2026-09-07, authorised end to end by the owner. `CP-1` SIGNED;
  `CP-2` HELD, superseded by `D-EU-109 f`'s corrected removal criterion. The merged `T03m` re-emission
  (`D-EU-109 g`, folding in `D-EU-107` and `D-EU-108`) writes to
  `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_final_2026-09-07/` and is running as of 2026-09-07 for
  `ES-MAD` and `IT-BOL`; the merged Speed campaign (T06) has not yet been submitted.

Everything else runs without a check-in, per the owner's standing "continue to the end" instruction.

---

## 6. Where things are

| What | Where |
|---|---|
| Plain-language brief | `BRIEF_european_locations_v5.md` |
| Progress checklist | `CHECKLIST_european_locations_v5.md` |
| 🔴 Operating prompt, live front | `prompts/DIRECTOR_PROMPT_group_floor_planning_2026-09-01.md` |
| Arc error index (`D-EU-52`) | `debugs/DEBUG_REFERENCES_european_locations.md` |
| Repo-wide error index | `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` |
| Live rules — eleven group sheets | `rules/RULES_dwelling_layout_groups_nocore_2026-09-03.html` (seven checks, `C11`, grid-first; the `2026-09-02` six-check version is archived) |
| Live rules — scheme, acceptance, context | `rules/RULES_dwelling_layout_scheme_nocore_2026-09-03.html`, `rules/EXAMPLE_dwelling_layout_validation_nocore_2026-09-03.md`, `rules/RULES_context_geometry_simulation_nocore_2026-09-03.md` (the three `2026-09-02` versions are archived) |
| Core-era rules (frozen, read-only) | `rules/archive/` |
| Test sheets, 550 plates | `rules/tests/TEST_0*_nocore_*.html`; superseded builds in `rules/tests/archive/` |
| Test JSON (census source, **never globbed**) | `openubem/outputs/eu_evidence/EU-21/rules_tests/test_0N_nocore.json` |
| The only script the arc writes | `scripts/eu21/07_nocore_tests.py` |
| Parked corridor cutter (intact, do not run) | `scripts/eu21/05_group_cutters.py`, plan `implementation/PLAN_eu21-cutter-2026-09-02.md` |
| Morphology census, 2,544 rows | `openubem/outputs/eu_evidence/EU-20/morphology_census.csv`, `representatives.json` |
| Layout engine (**still core-era, not yet updated**) | `openubem/geometry/european_residential.py` |
| IDF build + reroute | `scripts/run_eu_s2_campaign.py:516-534`, `openubem/idf/surfaces.py:640` |
| District campaign + manifests | `scripts/run_eu_s2_district_campaign.py` (areas `:408-418`) |
| Emitted IDFs + `prepared_buildings.csv` | `openubem/outputs/eu_evidence/EU-11/`, `EU-17/<district>/` |
| Floor-plan pages, geometry only (`D-EU-54` **closed 2026-09-07**, `D-EU-90`) | `plans3D/` (active `*_nocore_2026-09-03_r5.html`; baseline, `_r2`, `_r3` and `_r4` all in `plans3D/archive/` — 16 files, none overwritten; pre-T12 in `plans3D/previous/`; entry table `plans3D/index.html`) |
| 3D viewers, EUI colour + EU-21 checks merged on top of the same geometry | `outputs_3D/eu_<district>_viewer.html` (mirrored `openubem/outputs/3D/`), built by `scripts/generate_eu_3d_viewers.py`, plan `implementation/PLAN_eu-viewer-eui-floorplan-2026-09-07.md` |
| Superseded v4 trio (historical) | `previous/STATE_european_locations_v4.md`, `previous/BRIEF_european_locations_v4.md`, `previous/CHECKLIST_european_locations_v4.md` |
| Append-only progress log | `content/walkthrough_progress_log.csv` |
| Progress board (update in place) | `https://claude.ai/code/artifact/080bec44-ec13-4669-94db-8bb4a7a6763f` |

**Suite baseline:** last recorded full run, `pytest -q tests/` (T15, 2026-09-01) → **5 failed / 2,540
passed / 55 skipped**. The parallel baseline `pytest -q -n 8 tests/` → 2,345 passed / 55 skipped
(2026-08-28) predates it. Cite the enumerated 55-skip list, never the bare count. ⚠ Two pre-existing
failures in `tests/test_eu_real_footprint_feasibility.py` are known and untouched (`EU-13B` §10).

---

## 7. What happens next

0. **Completed:** `implementation/PLAN_eu21-district-viewer-2026-09-03.md` (`D-EU-88`, `D-EU-89`, `D-EU-90`) —
   T01–T05 complete and audited: EU-11 modal pop-up active, four district viewers built as `*_nocore_2026-09-03_r2.html`
   with generic fallback for all 1,641 uncatalogued buildings (0 massings remaining), baseline files archived in
   `plans3D/archive/`.
1. **Complete:** `implementation/PLAN_eu21-compactness-2026-09-03.md` — T01 … T07 done, `CP-3` reached
   2026-09-03. `C11` scored, grid-first search (`D-EU-83`) plus depth-layered, ring-radial and per-wing
   candidates (`D-EU-86`, `D-EU-89` clause 2) wired into `build_flats`, `C10` rebuilt as a created-pinch
   test (`D-EU-87`). **`MAX_FLAT_ASPECT` is not calibrated** — no rung of 2.5/3.0/3.5/4.0 reached `FAIL 0`
   after two genuine repair rounds; per `D-EU-89` clause 2 it is set to the strictest rung, **2.5**, and 81
   of 550 plates ship as an honest residual `FAIL` (57 unique buildings — thick-band courtyard rings and
   dense `n = 12` multi-wing plates whose wings do not separate under `lobes_of`). The five sheets are
   `TEST_0*_nocore_2026-09-03_r2.html` (the sole live set — the owner-read `2026-09-03`, no `_r2`, and the
   `2026-09-02` sets are both archived, `FINDING 239`: three of the five `2026-09-02` originals were
   overwritten in place before the archive and no longer show the delivered drawings). The four rules docs
   are re-dated `*_nocore_2026-09-03.*`. **`D-EU-84` is CLOSED 2026-09-08 as an accepted named residual
   (`D-EU-110`, §4)**: criterion 3 is satisfied by that ruling, criterion 2 (`FAIL 0` on 550 plates)
   remains **not met**, and the 81/550 plates over 57 buildings are carried as a declared limitation.
2. **Complete:** engine carry-in (`implementation/DONE/PLAN_eu-engine-nocore-carryin-2026-09-03.md`) — the
   proven cutter is live in `openubem/geometry/european_nocore.py`, bit-parity with `_r5` confirmed 0
   mismatches on 2,529/2,529 compared plates across all four districts. `CP-2` (the emitted-IDF audit)
   itself **FAILED** (`FINDING 249`/`250`) and was never re-signed — the owner lifted the wait-for-`CP-2`
   gate directly (`D-EU-100`, §4) rather than requiring a re-pass, so the campaign proceeded on the bit-parity
   result, not on `CP-2`.
3. **Complete:** `EU-18c`'s sample battery and `EU-19` (simulate) — the EU-11 ceiling82 harvest,
   closed 2026-09-06 (§8). Pooled EUI by district: London 97.081151, Lyon 65.935928, Madrid 77.153998,
   Bologna 54.935569 kWh/m². Both were waiting on `D-EU-55`, which the ceiling82 campaign's own submission
  ⚠ Lyon's 65.935928 is **superseded** by the 2026-09-07 T07 restatement, **69.595307 kWh/m² over 505 of 509** (`EU-11/FR-LYO-HAUTCOEURPENTES_merged_2026-09-07/summary.json`), and London's 97.081151 by **120.064327 kWh/m² over 706 of 706** (`EU-11/GB-LDN-STDUNSTANS_merged_2026-09-07/summary.json`), and Madrid's 77.153998 by **80.694006 kWh/m² over 1,166 of 1,175** (`EU-11/ES-MAD-BERRUGUETE_merged_2026-09-07/summary.json`); Bologna is still the ceiling82 number and remains stale pending its delta harvest.
   satisfies.
4. **Complete, `D-EU-105` (§8):** `D-EU-54` — the owner has now read the `plans3D/`-derived floor plans
   (via the merged `outputs_3D/` viewers) and confirmed, with one named exception carried as open work,
   never a blocker (`FINDING 258`, item 6).
5. **Complete:** `implementation/PLAN_eu-viewer-eui-floorplan-2026-09-07.md` — EU-11 EUI colour-by and
   EU-21 check badges merged on top of the EU-17-geometry 3D viewers, closed 2026-09-07 (§8).
6. 🔴 **Open, not scheduled — `FINDING 258`:** some buildings' floor-plan division is not homogeneous (a
   few tiny strip dwellings alongside one oversized dwelling absorbing the rest of the plate), even when
   the plate reports `PASS ALL 7 CHECKS` — the seven-check set does not penalize inter-dwelling area
   imbalance on the same plate. Owner ruling, verbatim: *"we can finish outputs^D then we can return this
   one, maybe for some buildings we need to re-design and re-simulate but not all batch, for some."* Any
   fix is **per affected building only** — never a full-batch re-cut or re-simulation.
7. Housekeeping, one pass, not urgent: `scripts/eu21/04_group_tests.py:184-192` still names the
   **core-era** test-sheet filenames as its outputs, so re-running `04` would resurrect sheets that were
   archived on 2026-09-03. Left as found; fix before `04` is ever run again.

---

**`D-EU-111` — best-effort tier for the three shape checks `C6`/`C10`/`C11`** (owner 2026-09-08, verbatim
*"ok, go for it. i accept D-EU-111."*; proposal in `debugs/DEBUG_floor-division-gap-and-clean-pipeline_2026-09-08.md` §4).
A cut that fails only a shape check is emitted with `fallback_reason = NOCORE_BEST_EFFORT_<ids>`, outcome
`DWELLING_LAYOUT_EMITTED_BEST_EFFORT[_IMPUTED_COUNT]`, amber badge in the viewer; `C1`/`C3`/`C4`/`C5`, the partition
audit and the density cap still refuse; `MAX_FLAT_ASPECT = 2.5` and every threshold unchanged (`D-EU-110` stands).
Executed by `implementation/PLAN_eu-recut-95pct-2026-09-08.md` T02.

**`D-EU-112` — neighbour imputation for the 585 never-simulated residential buildings** (owner 2026-09-08, verbatim
*"if possible, lets apply imputation and include these buildings inside the simulation clusters."* and *"please do it."*
on the explicit warning that this reverses `D-EU-101`'s no-imputation stance). Ladder: touching prepared neighbours
that agree → nearest prepared building within 30 m → district mode for the same type; fields: construction period,
storeys, dwelling count / typology; provenance `IMPUTED_NEIGHBOUR_*` / `IMPUTED_DISTRICT_MODE` on every row; never for
`IDF_ASSEMBLY_FAILED_*` (12 buildings). Supersedes `D-EU-101`'s *"no general imputation"* clause for these 585 only.
Building list with per-building proposal: `debugs/never_simulated_buildings_all_districts_2026-09-08.csv`. Executed by
`implementation/PLAN_eu-recut-95pct-2026-09-08.md` T04.

## 8. Progress log

Append-only, newest last. One entry per event that changed a number, a ruling, or an artifact.
Numbers here are the measured ones; the narrative-only version is `BRIEF_european_locations_v5.md` §6.

- **2026-09-01 — `EU-20` closed, `EU-21` opened.** All 2,544 census buildings sorted into eleven
  morphology groups. `EU-21` began: one cutting rule per group, graded on **550 real plates**
  (3/6/9/12 flats × eleven groups). No-core regime fixed as `D-EU-79` — dwellings only, no core, no
  corridor. The deliverable became the rules document; engine editing stopped.
- **2026-09-02 — the check set frozen.** Seven checks in force (`C1`, `C3`, `C4`, `C5`, `C6`, `C10`,
  `C11`). `C10` rebuilt as a *created-pinch* test (`D-EU-87`) after `FINDING 241` showed it had been
  reporting the widest place in a flat. `MAX_FLAT_ASPECT` pinned at **2.5** (`D-EU-82`, then `D-EU-89`
  clause 2 when no rung of 2.5/3.0/3.5/4.0 reached `FAIL 0`); 81 of 550 plates ship as an honest
  residual `FAIL` (`FINDING 242`). The threshold has not moved since, through every proposal to move it
  (`D-EU-84`, `D-EU-86`).
- **2026-09-03 (morning) — district viewers `_r2`, then the `MultiPolygon` fault.** `_r2` measured
  2,505 / 2,544 drawn (98.5 %), 2,235 passing (87.9 %). `FINDING 243`: 17 census buildings raised inside
  `build_flats` — a fault the 550 test plates never showed. Closed; runtime errors **17 → 0**, no purple
  building in any district. Rebuilt as `_r3` on the closed cutter; `_r2` archived on the owner's sentence.
- **2026-09-03 (colour repair) — `_r4`, accepted at `CP-3`.** Broader angle search, reflex-vertex
  boundary snapping, courtyard ring bisection at low `k` (160 of 509 failures recovered), and the
  `k > 12` refusal demoted to a scored attempt (`D-EU-92`, 8 of 23 pass). Result: **2,529 / 2,544 drawn
  (99.4 %), 2,178 passing (85.6 %)** — Madrid 867/961 (90.2 %) · Lyon 264/297 (88.9 %) · Bologna
  982/1,204 (81.6 %) · London 65/82 (79.3 %). Refused 23 → 15, `error = 0` in all four districts,
  no-regression gate **0 of 2,012**.
- **2026-09-03 — `FINDING 245`: the 95 % gate is unreachable as specified.** 187 plates fail `C11` at
  `k = 1`, where no cut was made and there is nothing for a slenderness check to judge. Post-waiver
  ceilings ((census − `C11`@`k=1`) / census) put every district under the bar. Put to the owner as
  `D-EU-93` — a scope question, never a threshold question.
- **2026-09-03 — `D-EU-93` taken.** *"yes lets go, i say yes D-EU-93, lets go"*. `C11` is not evaluated
  when the plate is undivided (`len(live) <= 1`); the aspect is still computed and shown, marked
  `(k=1, D-EU-93)`. `MAX_FLAT_ASPECT` stays **2.5** and `C11` applies unchanged at `k >= 2`. Carried into
  `scripts/eu21/07_nocore_tests.py` in three edits (`:969`, `:1643-1647`, `:1817`), cutter sha256
  **`fe75c96ed0ad8512a72c93fccd27b7e46b05c325911163bb47e41b1932a85717`**. Bench control
  (`--bench D_EU_93`): **200 / 200, 0 FAIL**; fail-set movement `C11` **263 → 76** (−187, the
  forced-by-definition `k = 1` count) with `C1`, `C3`, `C4`, `C5`, `C6`, `C10` all unmoved — the edit did
  exactly one thing.
- **2026-09-03 — `D-EU-94`: the simulation gate is armed.** *"ok once we reach 95, we will immediately
  start simulation on the speed cluster cloud computing"*. This satisfies `D-EU-55` for a future run; it
  is an arming, not a start order, and it does **not** clear the engine blocker —
  `openubem/geometry/european_residential.py` is still core-era (116 × "core", 26 × "corridor",
  **0** × "nocore"), so a campaign launched today would simulate the wrong layouts. `D-EU-54` (the owner
  reads `plans3D/` and confirms) is untouched and not consumed. Full ruling in §4.
- **2026-09-03 — `_r3` and `_r4` archived on the owner's sentence.** All eight pages moved to
  `plans3D/archive/`, which now holds 16 files (baseline, `_r2`, `_r3`, `_r4` × 4 districts); nothing
  overwritten (`D-EU-85`). `plans3D/` holds only `index.html`, `archive/`, `previous/`. `index.html`
  repointed so `_r5` is the active viewer in all four rows, with `archive/`-prefixed links to every
  previous build. Citation sweep: `PLAN_eu21-colour-repair-2026-09-03.md:74`, `:647`,
  `PLAN_eu21-district-viewer-2026-09-03.md:426`, and §3 of this file all repaired to `archive/` paths.
- **2026-09-03 — the four `_r5` district builds landed, `CP-4` accepted.** `07_nocore_tests.py` on the
  `D-EU-93` cutter, sequentially over `ES-MAD-BERRUGUETE`, `FR-LYO-HAUTCOEURPENTES`, `GB-LDN-STDUNSTANS`,
  `IT-BOL-GALVANI2`, tag `2026-09-03_r5`, no `--overwrite`; exit 0, wall time 219–513 s per district.
  Measured: **2,529 / 2,544 drawn (99.4 %), 2,353 PASS (92.5 %)** — Madrid **916/961 (95.3 %)** · Lyon
  281/297 (94.6 %) · Bologna 1,085/1,204 (90.1 %) · London 71/82 (86.6 %). Gates: cutter sha256 identical
  in all four, `max_flat_aspect = 2.5`, `error = 0` ×4, no `ERROR` status anywhere, drawn and refused
  unchanged from `_r4` (2,529 / 15), **no-regression 0 of 2,178**, and the four pages carrying tag, sha
  and the `(k=1, D-EU-93)` marker. PASS delta **+175, matching the pre-build projection district for
  district**; `C11` 263 → 76 with every other check unmoved. **`_r5` is now the build to quote** (§3).
- **2026-09-03 — 🔴 the 95 % gate is met.** Madrid crosses at **95.3 %**, three plates over its bar of
  913. Under `D-EU-91`/`D-EU-94` any one district crossing opens the simulation gate, read on `PASS` over
  `census_rows`. **The gate being open does not make a run correct**: the engine blocker of `D-EU-94`
  clause 3 stands unchanged — `openubem/geometry/european_residential.py` is still core-era, so the
  carry-in is now the single critical path, and `D-EU-54` is still unconsumed.
- **2026-09-03 — what stands between here and 95 % in the other three.** Lyon needs **2** plates and is
  the only cheap one; Bologna needs **59** and holds exactly 59 `C11` failures at `k >= 2` (thick-band
  courtyard rings and dense multi-wing plates whose wings do not separate under `lobes_of`) plus 27 `C10`
  and 20 `C5`; London needs **7** but has only 1 `C11` and 3 `C10` failing — **7 of its 11 misses are
  `k > 12` refusals**, so London cannot reach the bar through the checks at all and would need the
  refusal path reopened. None of these is reachable by moving `MAX_FLAT_ASPECT` (`D-EU-84`, `D-EU-86`).
- **2026-09-03 — the owner ordered the run and left.** *"lets go, to the end, no more ask, when you are
  satisfied, start simulations, i will go out i please continue"*. This is the owner's own sentence for
  `D-EU-55`, but it is **conditional on the director being satisfied**, and the director is not satisfied
  while the engine is core-era (`D-EU-94` clause 3). The answer given: there is room left to reach 95 % in
  the other three, but 95 % is no longer the blocker — the engine is.
- **2026-09-03 — `D-EU-95` ruled and the carry-in plan opened.** `implementation/PLAN_eu-engine-nocore-carryin-2026-09-03.md`.
  The engine carry-in is an **extraction**, not a re-implementation: the proven cutter is copied into a new
  `openubem/geometry/european_nocore.py`, and its acceptance test is **bit-parity with `_r5`** over all 2,544
  census plates — 0 mismatches or the plan does not continue. Measured seam: the whole IDF path goes through
  the single per-storey function `generate_european_ruled_storey_layout` (`european_residential.py:1083`), and
  `european_building_layout_to_zone_specs` (`:2701`) already emits **no** circulation zone when
  `circulation_polygon is None` — so the no-core regime reaches the IDFs with **no edit to the zone writer at
  all**. Tasks: `T01` extract · `T02` parity harness · `CP-1` · `T03` engine seam · `T04` regression sweep ·
  `T05` rebuild the four districts' IDFs into **new** dated directories (`D-EU-85`) · `CP-2` · `T06` the Speed
  campaign, director only, `sbatch --array`, `--time=7-00:00:00` on the CLI.
- **2026-09-03 — 🔴 `FINDING 246`, found before a line of code was written.** The district census cuts each
  building **once** at `k = round(dwellings_total / storeys)`; the engine cuts each **storey** at its own
  conserved allocation, and **1,814 of 2,544 buildings (71.3 %)** carry more than one distinct count — Madrid
  524 · Lyon 184 · London 68 · Bologna 1,038. Those are cut at two counts and carry plans only if both
  pass. So **`_r5`'s 2,353 `PASS` is a per-plate figure, not a prediction of the IDF outcome**, and `_r5` is not
  dwelling-conserving while the engine is. Nothing is changed to make the two agree — conservation is a real
  guarantee, the census's uniform `round()` is not, and `D-EU-88` clause 1 bars redistributing `k`. Instead a new
  task `T05a` measures the engine's own building-level census and reports it **beside** the census figure, never
  in place of it. The `D-EU-91`/`D-EU-94` gate was ruled and met on the census reading; this does not reopen it.
  Also carried into `T01`: the cutter must be fed a repaired, **centred** plate and the flats translated back,
  because `set_precision`'s millimetre grid does not land on the same bits at 4.5 × 10⁶ m as at the origin.
- **2026-09-03 — what a campaign would simulate *without* the carry-in, measured.** Read from the delivered
  core-era build's own `EU-11/<DISTRICT>/prepared_buildings.csv`: buildings carrying a real dwelling layout are
  Madrid **616 / 961** (64.1 %) · Lyon **198 / 297** (66.7 %) · London **40 / 82** (48.8 %) · Bologna
  **594 / 1,204** (49.3 %) — **fleet 1,448 of 2,544, 56.9 %**, with the other **1,096 buildings extruded as
  massing boxes**. `geometry_exclusions` is `{}` in all four, so no building was lost to an IDF-assembly crash
  and the `ZeroDivisionError`/`IndexError` demotion path (`run_eu_s2_district_campaign.py:434`) was never taken.
  This is the number the carry-in has to beat, and it is the concrete cost of submitting today.
- **2026-09-03 — Speed pre-flight, measured (login-node reads only).** `squeue -u o_iseri` → **0 jobs**;
  EnergyPlus 23.1.0 present at `/speed-scratch/o_iseri/openubem/tools/` (Ubuntu 20.04 and 22.04 builds);
  `/nfs/speed-scratch` 27 TB free of 121 TB; key-based SSH works with `BatchMode=yes`. Re-check the queue
  immediately before submitting.
- **2026-09-03 — pre-seam test baseline pinned, before `european_residential.py` was touched.**
  `python -m pytest -q -n 8 tests/geometry/ tests/test_eu*.py` → **6 failed, 613 passed** in 24.8 s. The six are
  named in the plan under `T04` step 1 (one `EU-15` ruled-coverage reflex case, three `EU-14B` Bologna
  layout-binding cases, two `test_eu_real_footprint_feasibility` fail-closed cases). They are class **(c)** by
  construction, so a seventh failure after the seam is unmissable and cannot be argued as pre-existing.
- **2026-09-03 — the first `CP-1` failed, and the harness was the fault, not the extraction.**
  `T01` produced `openubem/geometry/european_nocore.py` (1,731 lines) and `T02` produced
  `scripts/eu21/09_engine_parity.py`. The first run reported **1 verdict / 0 count / 53 check / 51 geometry**
  mismatches over 2,529 plates. Cause: the plan's own `T02` §1 told the harness to rebuild each plate's input
  from `plate["footprint"]` in the `_r5` JSON — but that field is the cutter's **output** plate and it is stored
  **rounded to 3 decimals**, so the harness was cutting a millimetre-perturbed polygon and comparing it to a
  full-precision result. Verified directly by the director on the two buildings the run named: fed the real
  input, `way/391270221` returns to `FAIL` and matches `_r5`. `T02` §1 is corrected — the harness now takes
  `geoms[(district, building_id)]` from `M07.load_universe()` and lets `cut_storey_nocore` do the repair and the
  centring once. **The gate did not move: still 0 mismatches of all four kinds.** The instability the failure
  exposed is recorded as `FINDING 247` and is deliberately **not** repaired — `D-EU-95` requires the extraction
  to reproduce `_r5`, including this.
- **2026-09-03 — ✅ `CP-1` SIGNED. The engine now has a cutter that is bit-identical to the accepted build.**
  Second parity run, corrected input: Madrid 955 · Lyon 295 · London 75 · Bologna 1,204 — **fleet 2,529 plates
  compared, 0 verdict / 0 count / 0 check / 0 geometry mismatches, 0 inputs missing.** Audited by the director
  rather than taken on the executor's word: `plates_compared` equals each district's `status == "direct"` count
  read from the `_r5` JSONs; the harness still carries `GEOM_TOLERANCE_M2 = 1e-6`, all seven `CHECK_IDS` compared
  on both `pass` and `show`, no skip list, no exemption, no `MAX_FLAT_ASPECT` reference. The geometry match is
  exact rather than merely within tolerance — the cutter's output is `set_precision`-snapped to the millimetre
  grid, and all 14,116 stored Madrid coordinates lie exactly on it. `D-EU-95` is satisfied on its own terms:
  `openubem/geometry/european_nocore.py` (1,731 lines) reproduces `_r5` plate for plate, verdict for verdict,
  check-string for check-string. T03 released.
- **2026-09-03 — ✅ `T03`/`T04` done and audited. The engine now draws the accepted no-core plans by default.**
  `generate_european_nocore_storey_layout` wraps `cut_storey_nocore` and `EUROPEAN_LAYOUT_REGIME = "nocore"` is
  the default; the corridor path is parked behind `"ruled"`, nothing deleted. The seam is one new function plus
  one three-line branch in `_layout_for` — **the zone-spec writer was not touched**, exactly as the call-graph
  reading predicted. Test suite re-run by the director, not taken on report: **6 failed, 613 passed**, the same
  six names as the pre-seam baseline, no seventh failure and no baseline test flipped. T03 introduced six new
  failures, all class **(a)** — tests that assert the corridor regime (a circulation zone exists, conditioned <
  gross because a core is carved, circulation coordinates are ring-stabilised). Each was pinned to
  `EUROPEAN_LAYOUT_REGIME = "ruled"` with `monkeypatch`; the diff was read and **no assertion was loosened**, no
  check touched, no `MAX_FLAT_ASPECT` reference added. Pinned to `"ruled"` those six reproduce circulation zones
  exactly, which is the proof the parked path still runs. The four `eu21` scripts show as modified in the tree
  but their mtimes are 2026-09-02 — untouched by this arc.
- **2026-09-03 — the seam smoke-tested end to end by the director, before the IDF rebuild was released.**
  A 24 × 18 m plate, 12 dwellings over 3 storeys: `dwelling_layout_emitted=True`, scheme `nocore_equal_area` on
  all three storeys, **12 zones and 0 `*_circulation` zones**, gross 1,296.00 m² == conditioned 1,296.00 m².
  This is the whole point of `D-EU-79` reaching the IDFs, demonstrated on the real engine entry point rather than
  inferred: `european_building_layout_to_zone_specs` emits a circulation zone only when `circulation_polygon is
  not None`, and the no-core path always returns `None`.
- **2026-09-03 — one real omission caught by the executor itself during `T01`**, worth recording because it would
  have been silent: `widest_fit` / `NARROW_PROBES_M` (`04_group_tests.py:296-303`) were missing from the first
  assembly pass, which would have dropped `_sweep_boundaries` from the candidate set through a swallowed
  `NameError` rather than an exception. Fixed before `T02` ran. This is exactly the failure mode the mechanical
  AST-closure step in `T01` exists to prevent, and it argues for keeping that step rather than eyeballing imports.
- **2026-09-04 — `T01`/`T02` of remedy plan `eu-nocore-finding249-remedy-2026-09-04` implemented and verified.**
  Restricted Option B remedy implemented in `scripts/run_eu_s2_campaign.py:94-141` (`_has_near_duplicate_vertex_surfaces`
  with `interzone_only=True`): partner-less collinear surfaces (Ground, Outdoors, Adiabatic) cannot cause EnergyPlus
  interzone mismatch fatal errors and are excused from `at_risk`. Interzone-paired defects keep setting `at_risk = True`
  unconditionally. Unit tests added to `tests/test_eu_s2_campaign.py:210-310` (17/17 passed clean, 0 regressions).
- **2026-09-04 — `T03` local EnergyPlus 23.1.0 regression validation: 16/16 clean runs.** The 16-building sample
  from Madrid (10), Lyon (5), and London (1) was rebuilt and simulated with EnergyPlus 23.1.0: 16/16 completed with
  Return Code 0, 0 Fatal, 0 Severe. Logged in `openubem/outputs/eu_evidence/EU-21/finding249_remedy_validation/T03_energyplus_validation_2026-09-04.json`.
- **2026-09-04 — `T04` full 4-district `CP-2` gate-5 re-audit measured: 🔴 `FINDING 250`.** Measured across all 2,262
  emitted-family buildings in `openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/`.
  Gates 1-4 ALL PASS EXACTLY: 0 circulation zones; route counts match 2,279 `T05a` EMITTED; gross == conditioned area;
  old-vs-new prepared buildings attribute diff 0/0/0. Gate 5: Reroute rate reduced from 57.7 % (1,306) to 50.2 % (1,135),
  recovering 171 real dwelling layouts (956 → 1,127). Residual 1,135 interzone-paired defects remain protected.
- **2026-09-04 — `D-EU-100` lifted the wait-for-`CP-2` gate, authorising immediate Speed submission.** The owner
  ruled explicitly to bypass gate 5 and proceed with cluster simulations in parallel.
- **2026-09-04 — `T05` packaging and transfer to Speed cluster completed.** All 4 district fleets staged, packed,
  shipped via `scripts/cluster/ship_eu11_fleet.sh`, and extracted at `/speed-scratch/o_iseri/fleets/EU11_<DISTRICT>_finding249_remedy_2026-09-04/`.
  Total: 2,527 IDFs verified on Speed (London 82, Lyon 293, Madrid 952, Bologna 1,200).
- **2026-09-04 — `T06` Speed cluster campaign SUBMITTED AND RUNNING IN PARALLEL across all 4 districts.**
  Submitted via `sbatch --time=7-00:00:00 --array=1-N%8` on partition `ps`:
  - `GB-LDN-STDUNSTANS`: Job ID **`1305158`** (82 tasks)
  - `FR-LYO-HAUTCOEURPENTES`: Job ID **`1305167`** (293 tasks)
  - `ES-MAD-BERRUGUETE`: Job ID **`1305176`** (952 tasks)
  - `IT-BOL-GALVANI2`: Job ID **`1305186`** (1,200 tasks)
  Total: 2,527 tasks, 32 active concurrent tasks executing across Speed and Magic worker nodes. Logs land at
  `/speed-scratch/o_iseri/openubem/fleets/%x_%A_%a.log`.
- **2026-09-04 — London (`GB-LDN-STDUNSTANS`, Job `1305158`) 100% completed, clean, and harvested.**
  All 82 tasks completed with Return Code 0, 0 fatal, 0 severe errors. Harvested into
  `openubem/outputs/eu_evidence/EU-11/GB-LDN-STDUNSTANS_finding249_remedy_2026-09-04/` (`gb_ldn_stdunstans_manifest.csv`,
  `summary.json`). District Mean Heating EUI: **87.34 kWh/m²**. Data and visuals updated in
  `docs/docs_ACTIVE/europeanLocations/outputs_3D/`: `eu_GB-LDN-STDUNSTANS_viewer.html` regenerated from the remedy
  IDFs with interactive no-core dwelling floor plans, and `buildings.csv` populated with simulation results.
- **2026-09-04 — Fleet progress & Antigravity update.** 317 tasks completed across the fleet (London 82/82,
  Lyon 103/293, Madrid 65/952, Bologna 67/1,200), 24 running, 12 failed geometry. Local monitoring stopped per
  owner order for an Antigravity software update. Speed cluster jobs continue running autonomously on partition
  `ps`. The next session resumes by running `.venv/Scripts/python.exe scripts/cluster/harvest_eu11_remedy_campaign.py --all`.
- **2026-09-04 — London viewer schema-mismatch bug found and fixed; EUI colour mode added.** The regenerated
  `eu_GB-LDN-STDUNSTANS_viewer.html` rendered fully blank: `scripts/update_eu_outputs_3d.py` emitted the scene-JSON
  provenance block as `provenance_counts`, but the shared viewer bootstrap (`scripts/generate_eu_3d_viewers.py`)
  reads `D.counts.measured` unguarded — `TypeError` threw before the building-draw loop ran. Fixed: renamed the key
  to `counts`, added the missing `data_dir` key. Registered in `debugs/DEBUG_REFERENCES_european_locations.md` §11.
  Also added a new `bU` "colour: EUI" mode + legend (viridis ramp over each district's simulated EUI range, grey
  for not-yet-simulated) to `generate_eu_3d_viewers.py` — applies automatically to all 4 districts on next harvest.
- **2026-09-04 — Owner scope ruling: fleet expands from census-only (2,527/2,544) to the full residential cadastral
  census (4,186), no building-type exclusion.** `D-EU-101`. Owner: *"of course, all types of residentials will be
  included no matter what their function is... this is same for other neighbourhoods as well."* Verified gap by
  direct tag cross-reference against `openubem/outputs/eu02/<district>/02_residential_manifest.gpkg`:
  `GB-LDN-STDUNSTANS` 1,242 total (house 1,018, apartments 182, residential 23, terrace 18, dormitory 1) vs fleet 82
  (apartments 73 + terrace 9 only, zero houses) — gap +1,160. `FR-LYO-HAUTCOEURPENTES` 530 vs 293 — gap +237.
  `ES-MAD-BERRUGUETE` 1,194 vs 952 — gap +242. `IT-BOL-GALVANI2` 1,220 vs 1,200 — gap +20. Combined gap **+1,659**,
  70 % concentrated in London.
  **Terminology reconciled** (three populations previously conflated in casual reference): "2,544 census fleet" =
  `EU-20/morphology_census.csv` rows (verified: exactly 2,544), the formal 95 % evaluation denominator that
  `build_flats` actually consumes (has `dwellings_total`/`storeys`/`idf_state`); "4,186 full cadastral fleet" =
  every OSM/cadastral building tagged residential regardless of type (STATE §table below); the buildings inside
  4,186 but outside 2,544 already carry a generic-fallback plans3D floor layout (`D-EU-90`) for visualization
  only — never an IDF, never an EnergyPlus run.
  🔴 **FINDING 251: classification/dwelling-count data does not exist for the +1,659 gap population.**
  `EU-20/morphology_census.csv` is exactly 2,544 rows — no entry for any gap building.
  `EU-04/observed_archetype_mapping_readiness.csv` (4,186 rows, verified) is stale/superseded: 3,888/4,186
  `EXCLUDED_MISSING_OR_AMBIGUOUS_INPUT`, only 297 `MAPPED_LAYOUT_READY` (all in Lyon, zero in Madrid/London/Bologna,
  verified) — yet those three districts already have hundreds of working IDFs today, proving this CSV is not the
  pipeline's real input.
  **New prerequisite task before any full-fleet IDF generation or Speed submission:** compute
  `dwellings_total`/`storeys`/`archetype_id` for the +1,659 gap buildings in `morphology_census.csv`'s exact schema.
  Current 2,527-task Speed campaign runs to completion first; this expansion is the next arc.
  See `CHECKLIST_european_locations_v5.md`, `eu-nocore-full-fleet-expansion` tasks.
- **2026-09-04 — `FINDING 251` T01, London fixed and verified: 82 → 389 buildings mapped (+307).**
  `_gb_rows` (`scripts/run_eu_s2_district_campaign.py:187`) never mapped OSM's `house` tag (1,018 of 1,242
  London buildings) to a TABULA building type at all — confirmed empirically by re-running `_gb_rows` against
  the full manifest and reading its exclusion `Counter`: `UNMAPPABLE_RESIDENTIAL_TYPE` 345 of 1,160 excluded
  (rest: 445 no EPC match, 355 EPC-period-straddle, 15 missing storeys).
  First attempt (`dwellings_total = 1` / blanket `"house": "SFH"`) was **wrong, caught before landing**:
  `openubem/semantic/european_archetype_mapping.py:28-30` documents why — OSM `house` cannot distinguish SFH
  from TH (materially different envelope heat loss), "must not be promoted... without supplementary evidence."
  Correct fix: split by footprint adjacency (`compute_footprint_adjacency`, already used for FR/IT) —
  `"TH" if is_attached else "SFH"`, same pattern as Bologna's `_it_rows:262-267`. Verified: all 307 newly-mapped
  London buildings are `TH`, zero `SFH` — architecturally correct for dense inner-London terraces (Tower
  Hamlets), a real sanity check that this isn't a guess. `tests/test_eu18c_viewer_geometry_only.py` (2 failures)
  and `test_eu_idf_plan_reader.py` (33 passed) re-run: the 2 failures are pre-existing and unrelated — that test
  asserts `outputs_3D` viewers carry zero EUI/kWh terms, a premise superseded once `update_eu_outputs_3d.py`
  started writing simulation results into that same path (§4 above: `outputs_3D/` = energy, by design) — not
  caused by this fix, needs its own owner decision to retire or rewrite, not touched here.
  **Not yet done:** Madrid (~81 buildings, same `house`/`residential` gap) — the shared
  `map_observed_building_to_tabula` only runs the two-signal adjacency derivation for `country == "FR"`,
  needs extending to ES plus a check that Spanish cadastral `observed_dwellings` data actually covers those
  rows. GB's remaining 445 (no EPC)/355 (period-straddle)/47 (no storeys) are genuine data gaps, not code bugs —
  owner call needed on imputation vs. accepting the ceiling. Registered:
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` ch. 6.
- **2026-09-04 (🔴 `FINDING 252`, plan doc + Antigravity prep dispatched)** — the `eu-nocore-full-fleet-
  expansion` CHECKLIST's original T01-T06 wrongly assumed the gap population needs a row in
  `EU-20/morphology_census.csv` and that the no-core cutter runs as a step separate from IDF generation.
  Verified by direct read: `scripts/run_eu_s2_district_campaign.py::prepare()` never touches
  `morphology_census.csv` — that file belongs only to the EU-20/EU-21 rule-grading pipeline (550 plates,
  the 95 % bar), a closed, separate artifact. `prepare()` reads the raw manifest directly (line 356-357),
  classifies inline (`_gb_rows`/`_it_rows`/`_mapped_rows`), and calls the already-carried-in no-core engine
  in the same pass (`_geometry()` line 112) — cutting and IDF-writing are one step, proven already by
  London's 82→389 recovery (no `morphology_census.csv` row was ever written for those 307).
  `PLAN_eu-nocore-full-fleet-expansion-2026-09-04.md` written with the corrected T01-T03 (extend the
  `FINDING 251` GB fix to ES — `map_observed_building_to_tabula`'s FR-only gate
  (`european_archetype_mapping.py:225`) widened to `("FR","ES")`, plus the missing ES `is_attached`
  assignment in `_mapped_rows` (`run_eu_s2_district_campaign.py:336-337`) that must ship with it or Madrid's
  gap buildings silently mislabel TH as SFH; re-run all four districts' `prepare()` into
  `*_full_fleet_2026-09-04/` output folders, never touching the live `*_finding249_remedy_2026-09-04/`
  campaign folders; audit and report, stop before packaging/Speed submission). Dispatched as a self-contained
  executor prompt (`prompts/EXECUTOR_PROMPT_full-fleet-expansion-2026-09-04.md`) to run in parallel with the
  current Speed campaign, so prepared IDFs are ready to package the moment it drains. Confirmed by direct
  read: Lyon (`_mapped_rows`) and Bologna (`_it_rows`) do not share GB's tag-mapping defect — their +237/+20
  gaps are expected to be real data gaps, out of scope for this fix.
- **2026-09-04 (🔴 `FINDING 253`, full-fleet prep T01-T03 complete, director-audited)** — Antigravity executor
  ran `PLAN_eu-nocore-full-fleet-expansion-2026-09-04.md` T01-T03. Audited against the repo, not the
  executor's own report: `git diff --stat` on the two allowed files shows exactly 2 files changed (12
  insertions, 3 deletions) — no other file touched, matching the plan's hard rule 1. All four
  `*_full_fleet_2026-09-04/summary.json` files read directly and match the executor's quoted numbers
  verbatim. Results: **London 82 → 389 (+307)**, **Madrid 952 → 1,008 (+56)**, Lyon 293 → 293 (+0), Bologna
  1,200 → 1,200 (+0) — Lyon/Bologna unchanged exactly as predicted (real data gaps, not code bugs). Fleet
  total 2,527 → 2,890 (+363 of the +1,659 gap; remainder is genuine missing source data — GB ~900 no-EPC/
  period-straddle/no-storeys, Madrid ~186 unresolved — owner call on imputation vs. ceiling still open).
  All four `prepare()` runs exited 0; no stop-condition (rule 4) was hit. Output confined to
  `*_full_fleet_2026-09-04/` folders; the live `*_finding249_remedy_2026-09-04/` Speed campaign folders are
  untouched (confirmed by `git status` — no changes under those paths). **Packaging + Speed submission of
  the expanded fleet remains blocked** on the current 2,527-task campaign draining (Lyon 122, Madrid 708,
  Bologna 1,063 tasks still pending+running as of the last poll) — director's job once both conditions clear.
- **2026-09-04 (🔴 FINDING 254, remaining full-fleet gap root-caused, no new code fix found)** — investigated
  the residual 1,296 (4,186 − 2,890) unresolved `blocker_exclusions` across all four `*_full_fleet_2026-09-04/`
  districts, each category checked directly against manifests/code, not taken on the investigating agent's word.
  1. `IDF_ASSEMBLY_FAILED_RuntimeError` (17: Madrid 9, Lyon 4, Bologna 4) — the catch site
     (`scripts/run_eu_s2_district_campaign.py:443-449`) carries an explicit design comment: geomeppy's
     `intersect_match` can fail numerically on a live noisy footprint even after both reroute safety nets in
     `openubem/idf/surfaces.py` give up, so that one building fails closed rather than aborting the district.
     Root-causing `intersect_match` itself is the pre-existing `T05-fix` item (§ above, "owner's call, not
     started") — not attempted here; a genuine gap given the closed-engine boundary.
  2. `TYPOLOGY_SIGNALS_DISAGREE` (Lyon 186) — reproduced live against Lyon's manifest: 176 of 186 are
     ordinary-looking 2–12-dwelling, 5–9-storey buildings (57/71/37/9/2 by storey, no outliers) that fall
     through `derive_bdtopo_building_type`'s three-bucket rule; 8 are `dwellings≥15 & storeys≤4`, 2 are
     `dwellings==1 & storeys≥5`. `tabula_archetypes_fr.json` carries no per-storey/dwelling threshold data to
     derive a widened rule from safely — extending the rule would set a new numeric threshold not grounded in
     any file already in the repo. **This is `D-EU-37` itself** (line 661 above), not a new question: the same
     unruled "extend the `D-EU-04-G` typology table" decision open since before v3, now against a smaller
     residual (186, down from 226) after unrelated fixes landed elsewhere.
  3. `MISSING_OBSERVED_STOREY_COUNT` (Madrid 163, London 47) — both manifests checked directly: `levels`,
     `height_m` and `roof_height_m` are all null on every affected row, `provenance_levels == "OSM_MISSING"`
     throughout. No fallback signal exists in either manifest. Genuine data gap.
  4. London `PERIOD_STRADDLE_*` (355) / `MISSING_OBSERVED_EPC_AGE_BAND` (445) — `GB_EPC_BANDS`
     (`run_eu_s2_district_campaign.py:63-64`) carries an explicit comment that EPC bands are intervals, not
     invented years, and a straddling band is excluded by design, not an oversight; Bologna's `_it_rows`
     (301-304) applies the identical pattern. The EPC join is an exact `osm_id` match with no fuzzy-match
     opportunity. Reversing either would overturn a standing, intentional fail-closed design, not fix a bug.
  **Bottom line: no new code-fixable bug found. 2,890/4,186 is a current count, not a ceiling** — the owner
  rejected that framing (2026-09-04): the only true ceiling is 4,186/4,186. Of the 1,296 remaining, ~1,027 are
  hard data gaps (17 crashes + 163 Madrid/47 London missing-storeys + 445 London no-EPC + 355 London
  period-straddle) that cannot move without fabricating source data. Lyon's 186 (176 of them one coherent,
  recoverable-looking shape) is **not** a hard gap — it is an open policy question, `D-EU-37`, awaiting the
  owner's ruling on a new typology threshold (see the decision request below). Investigation closed; the
  count moves further only if `D-EU-37` is ruled to extend the rule.
- **2026-09-04 (🔴 FINDING 255, `D-EU-37` ruled and implemented — Lyon +176)** — owner ruled *"100% full"* /
  *"make it possible"*: option 1 taken, not option 2. Plan `PLAN_eu-d-eu-37-lyon-mfh-widen-2026-09-04.md`
  dispatched to a fresh Sonnet executor; director-audited against the repo (diff + regenerated
  `summary.json`), not taken on trust. One line added to `derive_bdtopo_building_type`
  (`openubem/semantic/european_archetype_mapping.py:199-200`): `2<=dwellings<=12 & 5<=storeys<=9 -> MFH`.
  Re-ran Lyon's `prepare()` only, into the existing `full_fleet_2026-09-04` folder (hit and resolved a
  pre-existing, unrelated `schedule_dir.mkdir()` `FileExistsError` on re-run — script itself untouched, only
  the stale `idfs/`/`schedules/` output subfolders were cleared first). `population_prepared` 293→469 (+176,
  exact match to `FINDING 254`'s measured 176); `TYPOLOGY_SIGNALS_DISAGREE` 186→10 (the 8+2 out-of-scope
  outlier shapes, untouched, exactly as scoped). Fleet-wide: 2,890→**3,066/4,186 (73.2 %)**. Only
  `european_archetype_mapping.py` and Lyon's `full_fleet_2026-09-04/` folder touched; no other district, no
  other file. Still blocked on the live 2,527-task Speed campaign draining before the (now 3,066-strong)
  expanded fleet can package and ship.
- **2026-09-04 (🔴 FINDING 256, London EPC `construction_year` recovery — +30)** — the ceiling investigation
  (`debugs/docs/INVESTIGATION_full-fleet-100pct-2026-09-04_REPORT_claude-opus-5.md` §10, items b1/b2) found
  that the cached UK EPC certificates already carry an explicit `sap_building_parts[*].construction_year`
  that `_gb_rows` never read: it only ever looked at the RdSAP `construction_age_band` letter. Plan
  `implementation/PLAN_eu-epc-construction-year-2026-09-04.md` written by the director, executed by two
  fresh Sonnet sessions (T01-T03, then T04-T05), and re-derived off disk by the director rather than taken
  on trust. **What changed:** a new ingest script `scripts/ingest_gb_epc_construction_year.py` builds the
  sidecar `openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv` (1,336 rows /
  1,336 certificates / 67 `osm_id`s — the plan's pinned assertion, matched exactly), and a new
  `_gb_age_decision` helper (`scripts/run_eu_s2_district_campaign.py:171`) replaces the two bare `continue`
  lines at :182-187. Two admissions, both fail-closed: (b1) no age band at all, but every observed
  certificate year lands in one TABULA period → take it, stamped `EPC_OBSERVED_CONSTRUCTION_YEAR`;
  (b2) a straddling band whose observed years all fall inside the band *and* inside one period → take it,
  stamped `EPC_CONSTRUCTION_YEAR_RESOLVED_STRADDLE`. Contradicting years, cross-period years and years
  outside the band are all still refused — nothing is interpolated. `prepare()` is not edited. New test module
  `tests/test_eu11_gb_epc_construction_year.py`, 6/6 pass including both refusal cases.
  **Measured result**, read from a *new* folder `EU-11/GB-LDN-STDUNSTANS_full_fleet_epcyear_2026-09-04/`
  (the `full_fleet_2026-09-04` baseline was never overwritten and still reads 389): `population_attempted`
  1242 unchanged, `population_prepared` 389→**419**; `MISSING_OBSERVED_EPC_AGE_BAND` 445→418 (−27),
  `PERIOD_STRADDLE_K_GB.07_GB.08` 20→12 (−8), `MISSING_OBSERVED_STOREY_COUNT` 47→52 (+5 — the five named
  footprints `way/192335494`, `way/459203320`, `way/823489446/7/8` gain an age and then fail the *next* gate;
  a bucket move, predicted in the plan, not a regression), B/C/D/F/J straddles and
  `UNMAPPABLE_RESIDENTIAL_TYPE` all unchanged, no `IDF_ASSEMBLY_FAILED_*` key appeared. Every single number
  matched the plan's offline prediction. `construction_period_provenance` is populated on exactly 30 rows
  (24 + 6) and blank on the other 389. **Additivity proven, not asserted:** joining the two
  `prepared_buildings.csv` on `building_id` gives 389/389 matched rows and **0 `idf_sha256` mismatches**.
  Fleet-wide: 3,066→**3,096/4,186 (74.0 %)**. **Two things deliberately not done:** the new folder was not
  promoted over the baseline (director decision, and the live Speed campaign is still draining), and none of
  the `(c)` rulings were implemented. **The ceiling is now documented**, at the owner's request, in
  `DEBUG_why-not-100-percent-2026-09-04.md`: 100 % is unreachable and ≈3,430/4,186 (≈82 %) is the true
  maximum. The residual ≈750 is dominated by London — 418 footprints for which no EPC has ever been lodged
  (a UK certificate is only issued on sale, let or new build since 2008; 395 have a UPRN with no certificate,
  23 have no UPRN), plus 269 whose own certificates place them on both sides of a TABULA boundary (70) or
  leave them ambiguous (199). Reaching 100 % would require inventing a build year for buildings that have
  never had one recorded anywhere — which the investigation scope forbids and the pipeline is built never to
  do.
- **2026-09-06 — EU-11 ceiling82 harvest closed (`EU-19`, satisfies `D-EU-55`).** All 10 Speed jobs
  (backlog ×4, Step2-delta ×4, `FINDING-253`-remedy ×2) drained and merged by
  `scripts/cluster/harvest_eu11_ceiling82_final.py` against each district's `_ceiling82_2026-09-05/`
  final-population snapshot: London 451/451 run/success, 0 failed, pooled **97.081151 kWh/m²** · Lyon
  507/506, 1 failed, **65.935928** · Madrid 1174/1164, 10 failed, **77.153998** · Bologna 1212/1200, 12
  failed, **54.935569**. Total 3344 run / 3321 success / 23 failed — matches stop point 3's own population
  figure (3,344/4,186 = 79.9 %) and the arithmetic of the 30 originally-classified backlog failures minus
  the 7 `FINDING 253` stems fixed by the remedy. Hard stop-condition (>10 % measured-vs-predicted
  disagreement) never tripped: 23/3344 = 0.7 %. `scripts/generate_eu_3d_viewers.py` regenerated and
  mirrored for all 4 districts on the harvested data; noted in passing, not fixed here: the "colour: EUI"
  button already in the viewer template had no backing Python data (`b.eui` never set) — closed by the
  next arc, §8 2026-09-07 below. Full detail:
  ⚠ Lyon's **65.935928** above is superseded by the 2026-09-07 T07 restatement, **69.595307 kWh/m² over
  505 of 509** (`EU-11/FR-LYO-HAUTCOEURPENTES_merged_2026-09-07/summary.json`), London's **97.081151**
  by **120.064327 kWh/m² over 706 of 706** (`EU-11/GB-LDN-STDUNSTANS_merged_2026-09-07/summary.json`),
  and Madrid's **77.153998** by **80.694006 kWh/m² over 1,166 of 1,175**
  (`EU-11/ES-MAD-BERRUGUETE_merged_2026-09-07/summary.json`) —
  note the population changed too: the ceiling82 London number pooled 451 buildings, the restated one 706.
  `prompts/DIRECTOR_PROMPT_eu82pct-ceiling-harvest_2026-09-05.md`,
  `implementation/PLAN_eu-82pct-ceiling-2026-09-05.md`.
- **2026-09-07 — `D-EU-105`: `D-EU-54` closed.** Owner reviewed the merged `outputs_3D/` floor-plan
  modals (built on the same `plans3D/`-proven geometry) and ruled, verbatim: *"i am okay with plans pages
  mostly, except, [screenshot of `BATIMENT0000000240880367_part0`, Lyon] i am seeing that, some of them is
  not homogenously divided as floor plans as it should, lets not this one. we can finish outputs^D then we
  can return this one, maybe for some buildings we need to re-design and re-simulate but not all batch,
  for some."* Read as confirmation with one named, non-blocking exception, carried forward as
  `FINDING 258` below — not as a reason to keep the gate open.
- **2026-09-07 — `FINDING 258`: floor-plan division not homogeneous on some plates, despite
  `PASS ALL 7 CHECKS`.** Example: `BATIMENT0000000240880367_part0` (Lyon) — three tiny strip dwellings
  plus one large L-shaped dwelling absorbing the rest of the plate. The seven-check set (`C1`, `C3`, `C4`,
  `C5`, `C6`, `C10`, `C11`) has no check for inter-dwelling area balance on the same plate, so a valid,
  passing cut can still be visually lopsided. Open, not scheduled. Owner ruling: fix **per affected
  building only**, never a full-batch re-cut or re-simulation, and only after the viewer-merge arc below.
- **2026-09-07 — viewer EUI + EU-21 checks merge closed.**
  `implementation/PLAN_eu-viewer-eui-floorplan-2026-09-07.md`, T01–T03, all audited against the regenerated
  HTML directly, not taken on trust. T01: EU-11 `eui_kwh_m2` wired into the existing "colour: EUI" button
  (closes the gap noted 2026-09-06 above); hit a `pandas.DataFrame.iterrows()` dtype-upcast bug that zeroed
  Bologna's join alone (plain-numeric `building_id` upcast to float against a float sibling column) — fixed
  with `dtype={"building_id": str}` + `zip()`, registered in
  `docs/docs_EXPLANATION/OpenUBEM_debug_References.md:1040-1047`. T02: `08_district_viewer.py`'s
  `ZONE_COLORS` 12-hex cycle ported for `ruled` buildings. T03: EU-21 `checks`/`status`/`verdict` merged as
  annotation onto `pl_obj` (never overriding IDF geometry, rule 3) and the PASS/FAIL badge-chip banner
  ported into `openPopup`; checks-join 0 misses in all four districts (961/297/82/1204 hit), badge rendered
  only where `status=="direct"` (955/295/75/1204 of those); 8 spot-checked buildings (PASS+FAIL × 4
  districts) matched `PLANS_*_r5.html` exactly on verdict and full check-chip array, independently
  re-verified against the regenerated scene JSON, not just the executor's report. All 4
  `outputs_3D/eu_<district>_viewer.html` (+ `openubem/outputs/3D/` mirror) regenerated, primary/mirror
  pairs byte-identical. **This closes the viewer-merge arc and, with it, the four-step order in
  `BRIEF_european_locations_v5.md` §4.** Remaining open item: `FINDING 258` above.
- **2026-09-07 — `FINDING 259`: the viewer's grey is not the campaign's grey.** The
  `eu_<district>_viewer.html` pages drew geometry from the EU-17 rebuild tree while colouring EUI from the
  EU-11 ceiling82 tree — two different populations. Measured by direct file count: London 82 IDFs in the
  EU-17 tree vs. **451** actually simulated (under-reported by 369), Lyon 297 vs. 510 (213), Madrid 961 vs.
  1,181 (220), Bologna 1,204 vs. 1,216 (12) (`implementation/PLAN_eu-london-coverage-2026-09-07.md:18-31`).
  London's HUD line "1,160 have no IDF … shown grey" was true of the EU-17 tree and wrong as a coverage
  statement. Closed in T01: the viewer now resolves ceiling82-first, falls back to EU-17, and reports a
  fourth HUD state; post-change `simulated` counts (Madrid 1,174, Lyon 507, London 451, Bologna 1,212) all
  equal each district's `population_run` exactly (`CP-1` SIGNED, `:172-183`). No simulation and no
  published number changed — only what the viewer claims about itself.
- **2026-09-07 — `FINDING 260`: reserved, not yet populated.** `implementation/PLAN_eu-plan-homogeneity-2026-09-07.md:276`
  reserves `FINDING 260` for T07 ("register the outcome as `FINDING 260` if any measured behaviour differs
  from this plan's predictions"). T07 is director-only and folds into `D-EU-109`'s single merged Speed wave
  (`D-EU-107` §4 above), which has not run — no content exists yet.
- **2026-09-07 — `FINDING 261`: 45.6 % of the simulated fleet was simulated with no dwelling division at
  all.** Counted by grepping the emitted ceiling82 IDFs for a `…_F0_whole` zone and cross-checking against
  each district manifest's `geometry_outcome`; the two agree to the building, fleet-wide **1,524 / 3,344**
  (`ES-MAD` 642/1,174 = 54.7 %, `FR-LYO` 173/507 = 34.1 %, `GB-LDN` 49/451 = 10.9 %, `IT-BOL` 660/1,212 =
  54.5 %). By `geometry_outcome`: 1,239 `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` (layout was
  emitted, then force-rerouted to one zone per storey), 213 `FALLBACK_PENDING_LAYOUT_MISSING_DWELLING_COUNT`,
  72 `FALLBACK_PENDING_LAYOUT` (Madrid only). **1,167 of the 1,524 already have a valid, checked,
  multi-dwelling no-core cut on disk**; the remaining 357 are genuinely `k <= 1` and are not a defect
  (`implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md:42-64`, `CP-1` SIGNED `:406-417`).
- **2026-09-07 — `FINDING 262`: the imbalance `D-EU-107` measures is mostly invisible today.** **232 of the
  344** `D-EU-107`-affected plates (`ES-MAD` 88, `FR-LYO` 9, `GB-LDN` 1, `IT-BOL` 134) are also inside
  `D-EU-109`'s 1,524-building undivided set: they carry a valid imbalanced cut in the census but were
  rerouted to one zone per floor at emission, so no IDF in the current fleet expresses their imbalance —
  including the owner's own exemplar, `BATIMENT0000000240880367_part0` (`FR-LYO`, k=4, spread 0.0527)
  (`implementation/PLAN_eu-plan-homogeneity-2026-09-07.md:311-318`, `CP-2` SIGNED). Consequence, load-bearing
  not a preference: no `C12` improvement may be claimed from a pre-`D-EU-109` emission, which forces the
  landing order **`D-EU-109` -> `D-EU-107` -> `D-EU-108`**
  (`implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md:96-97`).
- **2026-09-07 — `FINDING 263`: the near-duplicate-vertex path is not deterministic.** The
  `D-EU-108` executor reproduced non-identical `idf_sha256` hashes for two rows on a same-process double
  build, with real ULP-level vertex and volume shifts and, in one case, an inserted wall surface with the
  subsequent walls renumbered (`implementation/PLAN_eu-london-coverage-2026-09-07.md:460-467`). Binding on
  the arc: `idf_sha256` is **not** a valid control over any building whose `geometry_outcome` is
  `*_INTERZONE_MISMATCH_REROUTED` or whose `fallback_reason` is `near_duplicate_vertex_tolerated_box` —
  **every hash gate in `D-EU-107`, `D-EU-108` and `D-EU-109` must exclude that population by name and state
  the excluded count**; a gate quoted `N/N` without naming the exclusion is not a passed gate. `D-EU-108`'s
  own control excluded 39 such London buildings and reported 412/412 over the rest. `D-EU-109`'s ring
  cleanup removes this machinery fleet-wide, after which the hash control becomes valid over the full
  population (`:467-474`).
- **2026-09-08 — `D-EU-110`: `D-EU-84` closed as an accepted named residual, and the layout side-car
  payload re-emitted for three districts.** Two events, one pass, both triggered by the 4J
  pre-registration's freeze conditions
  (`messages_GSSCanada/2026-09-08_4J_to_OpenUBEM_layout_payload_and_two_questions.md`).
  **(a) The ruling.** `D-EU-84` demanded a calibration of `MAX_FLAT_ASPECT`; the ladder was run over all
  550 plates and no rung reached `FAIL 0` after two genuine repair rounds (`FINDING 242`), so per
  `D-EU-89` clause 2 the constant sits at the strictest rung, **2.5**. That outcome *is* the answer and is
  accepted as such: `D-EU-84` is closed, the residual is named and carried (**81 of 550 plates over 57
  unique buildings** ship an honest `FAIL`), `EU-21` acceptance criterion 3 is satisfied as a declared
  residual while **criterion 2 (`FAIL 0` on 550 plates) remains not met**, and the threshold stays frozen
  against accommodation (§4, §5, §7).
  **(b) The re-emission.** The shipped `layouts/` payload was a *different population* from the district
  it sat beside: `scripts/generate_eu_3d_viewers.py:1307-1314` copies `EU-17/<district>/layouts` verbatim
  into `outputs_3D`, and the EU-17 manifests are partial rebuild scopes — Madrid 961, Lyon 297, London 82,
  Bologna 1,204 files against declared populations of 1,175 / 459 / 706 / 1,211. `sources.json` therefore
  described the published district while the folder beside it described the EU-17 rebuild scope. Re-emitted
  from the current published trees (ES/GB `*_merged_2026-09-07`, IT `*_final_2026-09-07`) into fresh
  staging trees `EU-11/<D>_layouts_2026-09-08/`, emitting against a **copied** manifest so no published
  artifact was mutated, then installed into `outputs_3D/eu_<D>_data/layouts` and the
  `openubem/outputs/3D/` mirror — `layouts/` only, no `buildings.csv`, `viewer.html`, `sources.json` or
  `index.html` touched. Audit, measured per line, emitted / docs / mirror / `has_unconditioned_core: true`
  / `circulation_area_m2_total == 0`: Madrid **1,175 / 1,175 / 1,175 / 0 / 1,175**; London
  **451 / 451 / 451 / 0 / 451**; Bologna **1,211 / 1,211 / 1,211 / 0 / 1,211**; `diff -rq` staging vs both
  installs clean in all three. Named fallbacks — Madrid 75 `FALLBACK_PENDING_LAYOUT` (35 `C10`, 13 `C11`,
  9 density > 12, 8 `C4`, 5 `C5`, 4 `C6`), London 12 (7 density > 12, 3 `C10`, 2 `C11`), Bologna 175
  (106 `C11`, 33 `C10`, 24 `C5`, 8 `C6`, 3 `C4`). Lyon was **not** re-emitted: 4J is a physical baseline
  there and never enters a 4J denominator.
  **Two residuals carried out of this pass, neither fixed:** (i) **London ships 451 side-cars for 706
  simulated buildings.** The emitter's `row_map` is the intersection of `_gb_rows(gdf, records)` with the
  simulated ids (`scripts/emit_eu11_layout_sidecars.py:207`), and `_gb_rows` yields no record for 255 of
  them — the London coverage-recovery batch (commit `4431f2fe`), identifiable in the manifest as the rows
  carrying `platform`/`energyplus_version` but no `run_seconds`. Their `geometry_outcome` in the manifest
  is stale carry-in, which is why the manifest reads 691 `DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT` against
  451 non-empty `layout_json`. Any quotation of London layout coverage must say **451 of 706**. Those 255
  are **not** a permanent limitation: they are exactly `D-EU-108`'s newly admitted London population
  (187 age-inherited + 68 straddle-disambiguated) and they are inside the merged `D-EU-109` re-emission +
  1,534-case Speed campaign, which has not run
  (`implementation/PLAN_eu-dwelling-division-recovery-2026-09-07.md:100-102`, `:392`). London layout
  coverage will therefore move once that campaign lands, and every downstream consumer holding a frozen
  London population must be told before it does.
  (ii) **`sources.json` `layout_counts` / `layouts_coverage` are unchanged and now disagree with the
  payload** — Madrid `ruled 1038`, London `ruled 692`, Bologna `ruled 552`. Those counts are derived from
  the viewer's per-building render mode in `buildings.csv`, not from the side-car file count, so patching
  them in place would only move the disagreement onto `buildings.csv`; the correct repair is a viewer
  regeneration, which is not authorized here and would rebuild delivered artifacts. Left untouched and
  named.
- **2026-09-08 — `FINDING 266`: `units_per_floor` in the layout side-car is a MAXIMUM, not a constant;
  `units_per_floor x storeys` is not a population and over-counts on 1,480 buildings.** Raised by 4J from
  outside the codebase and re-measured here directly on the installed payload: `units_per_floor` equals
  `max(floors[].dwelling_count)` on **100 % of the files that carry it** — Madrid 1,100/1,100, London
  439/439, Bologna 1,036/1,036 — while **1,480 of the 2,484 multi-storey buildings** (Madrid 553 of 1,032,
  London 47 of 437, Bologna 880 of 1,015) have a non-uniform per-storey dwelling count. The only
  authoritative per-storey number is `floors[].dwelling_count`, and the only authoritative building total
  is its sum. This is the shipped-artifact face of `FINDING 246` (the census cuts one `k` per building, the
  engine cuts one `k` per storey), and 4J confirmed the identity from outside without reading our code: the
  count of buildings where a single building-level `k x storeys` fails to reproduce the emitted zone count
  is **exactly** the non-uniform count, district by district — Madrid 1,100 − 547 = 553, London
  439 − 392 = 47, Bologna 1,036 − 156 = 880. Independent confirmation, not a defect on either side.
  Also verified by 4J across all 2,837 installed files: `conditioned_floor_area_m2 / gross_footprint_area_m2`
  has min **1.000000** and max **1.000000**, zero files outside a 0.999–1.001 band — a stronger external
  control on `D-EU-80`'s every-square-metre-is-a-flat premise than anything run on this side.
