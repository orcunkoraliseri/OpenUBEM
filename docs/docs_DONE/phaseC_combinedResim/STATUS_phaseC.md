# Phase C — STATUS HUB (read this one first)

> **This is the single doc to progress Phase C from.** It says where we are, what's next, and which
> supporting doc to open *only when executing*. Last updated: 2026-06-19 (manager).
>
> Why there are several files in this folder: each plan is a *persistent execution record* with its own
> progress log (project convention — we don't delete them). Two are DONE history, one is a deliverable,
> one is the live next action. This hub is the map over all of them.

---

## 1. Phase C in one paragraph

Re-simulate the 12 validation cells (NYC·LA·Austin × centre·urban·suburban·rural) with **fresh IDFs**
carrying BOTH calibration fixes — multi-floor zoning + real DOE schedules — plus the new core/perimeter
geometry repairs, then **re-score against the V17 measured anchors (V19)**. The pilot (la_urban) is
closed clean. The 12-cell fan-out is done except **3 cells** that need a geometry fix-batch + one
missing config before they can complete. After all 12 land, V19 re-scores and the final report updates.

---

## 2. The four supporting docs — what each is, and its status

| Doc | Role | Status |
|---|---|---|
| `PLAN_phaseC-combined-resim.md` | **Umbrella plan** — the whole Phase C resim (zoning + schedules → resim → V19). | Pilot (P1) GREEN; fan-out (P2) mostly done; V19 (P2.T04) pending the 3 cells. |
| `PLAN_coreperim-degenerate-fix.md` | **DONE history** — original 3-guard geometry detector (the first 3 pathology classes). | ✅ Complete (T01–T06, all audited). Reference only. |
| `PLAN_phaseC_geometry_fixbatch.md` | **← THE LIVE NEXT ACTION** — extends the detector to the new pathologies + harness hardening + nyc_centre + re-run the 3 cells. | Plan READY (T01–T10). **Not started.** |
| `REPORT_phaseC_pilot.md` | **Deliverable** — la_urban pilot 3-way comparison (old vs zoning-only vs combined). | ✅ Written. Reference only. |
| `deepResearch/RESULT_1/2/3` | **Literature/tooling review** validating the repair strategy. | ✅ Complete (see §4). |

**If you only open one doc to execute: open `PLAN_phaseC_geometry_fixbatch.md`.** Everything else is
context or history.

---

## 3. Where we are (the live picture)

- ✅ **ALL 12 of 12 cells clean** (parse 100%, zone-integrity 0, apt lighting 3.965, zero exclusions).
- ✅ **The final 3 cells closed 2026-06-19** by the geometry fix-batch (T10), each PASS on the full gate:
  - `austin_urban` — 425/425, job 979381. Prior sliver-perim + MultiPolygon crash now reroutes.
  - `la_centre` — 226/226, job 979819. Prior interzone-mismatch + thermal-divergence now reroute (not dropped).
  - `nyc_centre` — 738/738, job 980072. New cell (T08) ran clean first-pass.
- ▶️ **V19 re-score is now UNBLOCKED** — full 12-cell set landed (LA set complete) → next action is the
  city-level re-score vs V17 anchors ("is LA still +40% hot after the zoning fix?").

---

## 4. Deep-research verdict (the "do we need a better repair?" question — answered)

Three deep-research reports (`deepResearch/RESULT_1/2/3`) reviewed how mature tools handle this and what
the fallback costs. **Bottom line: our fallback approach is the industry standard and is defensible —
ship it as planned. A higher-fidelity option exists but is optional and out of scope.**

- **Fallback to one-zone-per-floor is standard practice** — Sefaira, CityBES, AutoBEM, URBANopt all do
  exactly this when core/perimeter zoning fails (RESULT_1 §9, RESULT_3 §5).
- **Accuracy cost is negligible at our scale** — <2% of footprints affected; **aggregate city-EUI impact
  <0.1%**, far under ASHRAE Guideline 14 tolerances. *(Directly citable in V19/final report — RESULT_3
  Defensibility Verdict.)*
- **Our diagnosed crashes are confirmed verbatim** — geomeppy's uncaught `IndexError` (narrow core) and
  MultiPolygon `NotImplementedError` (RESULT_2 §2.4) — validating fix-batch T02/T03.
- **Detector thresholds corroborated** — shoelace winding, min-zone-area, vertex-collapse are all
  established sliver criteria; T04's 0.5 m² floor is conservative and safe (RESULT_2 §3.1).
- **Optional future upgrade (NOT now):** pre-simplify (Douglas–Peucker) + pyclipper offset + sliver-merge
  would *retain* core/perimeter on most odd buildings (RESULT_2 ranked #1, permissive-license, pyclipper
  already a dependency). Tracked as a post-Phase-C enhancement only.
- **Side note for the LA question:** single-zone fallback *underestimates* loads, so it is **not** a
  candidate cause of LA running hot — and it touches too few buildings to matter either way.

→ **No change to the repair plan's approach was warranted; the fix-batch (`PLAN_phaseC_geometry_fixbatch.md`)
stands as written**, now annotated with this corroboration (its §1 callout). The optional fidelity upgrade
is logged there too, not adopted.

---

## 5. Next actions (progress from here, in order)

1. [x] **Execute `PLAN_phaseC_geometry_fixbatch.md` T01–T09** (code + tests) — DONE 2026-06-19, full
   suite green (21 + 50 passed). CP-A/CP-B/CP-C all cleared.
2. [x] **Manager-launched cluster re-run (fix-batch T10):** austin_urban + la_centre + nyc_centre →
   DONE 2026-06-19, **12-cell set complete, zero exclusions.** R5 baselines untouched.
3. [x] **V19 re-score — DONE 2026-06-20.** Verdict shipped: `docs/docs_VALIDATION/overAll/V19_phaseC_rescore.md`
   (Sonnet ran Phase 1 over all 12 cells; manager wrote the verdict). **Findings:** the fixes worked where
   V17 flagged over-prediction — NYC multifamily +33.5 %→**+0.7 %**, food-service +110/+160 %→**−1.6/+12 %**,
   NYC city aggregate **+10.0 %** (still a pass). The V17 "NYC office −0.3 % anchor" was **partly a V18
   artifact**: with the ÷n_floors defect fixed, office rose to **+37 %** → office is the NEW P1 systematic
   bias (all cities +30–52 % vs ESPM). **LA is still hot (+38.8 %, unmoved −0.6 %)** → confirmed a real
   climate/HVAC problem, NOT the zoning defect. Calibration P1 = office loads + LA climate (user go/no-go).
4. [ ] **Cross-case synthesis + final report** update (extends V13 / `REPORT_R5_final.md`).

**Standing constraints:** manager writes/audits plans (no feature code); fresh Sonnet executes; cluster
runs are user go/no-go and manager-launched (login-node rule); gates report-only.

---

## 6. Pointer

This hub mirrors the Phase C slice of the master checklist (`docs/PROJECT_CHECKLIST.md` §B/§C). Keep both
in sync; the checklist is the cross-project surface, this hub is the Phase-C working map.
