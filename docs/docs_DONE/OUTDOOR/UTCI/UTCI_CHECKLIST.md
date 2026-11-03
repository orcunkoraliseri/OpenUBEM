# UTCI / Stage-6 Outdoor Microclimate — Arc Checklist

**One-screen tracking surface for the whole UTCI arc.** Read this first when you open
`docs/docs_DONE/OUTDOOR/UTCI/`. Last updated 2026-07-25.

> 🗄️ **ARCHIVED 2026-07-25.** This arc is closed and the folder moved
> `docs/docs_DONE/OUTDOOR/UTCI/` → **`docs/docs_DONE/OUTDOOR/UTCI/`**. Nothing here is live work.
> The platform-level description of what Stage 6 does now lives in
> `docs/docs_EXPLANATION/OpenUBEM_fundamentals.md` §11 and
> `docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md`.

| | |
|---|---|
| **Arc status** | ✅ **COMPLETE + ARCHIVED** — T01–T26 done, CP-1…CP-5 all signed (CP-5 signed 2026-07-24) |
| **Follow-on work** | ✅ **ALL CLOSED.** E-UTCI-09 investigation COMPLETE (§3) → E-UTCI-09 height backfill plan (§3b) **CP-C SIGNED 2026-07-25, plan closed** — three flat-field cells cleared, rural residual documented and forwarded out of this arc |
| **What still leaves this arc** | 3 forwarded defects (E-UTCI-12, E-UTCI-13, and the rural `height_m` residual) belong to whichever arc next owns Stage-1 acquisition / Stage-2 imputation — **not** to Stage 6 |
| **Binding record** | `implementation/PLAN_utci_microclimate_implementation.md` (frozen — cite, never edit) |
| **What it produces** | `06_*` artifacts + figures in `openubem/outputs/` — a *separate analysis product*, it changes no EUI baseline |

---

## 1. Build phases — T01 → T26

| Phase | Tasks | Checkpoint |
|---|---|---|
| **Phase 0 — Foundations** | `[x]` T01 package skeleton · `[x]` T02 EPW hourly parser · `[x]` T03 psychrometrics · `[x]` T04 solar position | — |
| **Phase 1 — UTCI kernel** | `[x]` T05 Bröde 210-coefficient polynomial · `[x]` T06 reference-table exactness gate · `[x]` T07 stress categories & official palette | ✅ **CP-1 SIGNED** 2026-07-23 |
| **Phase 2 — Spatial domain & geometry** | `[x]` T08 raster domain builder · `[x]` T09 vegetation layer (tiered, opt-in) · `[x]` T10 sky view factor & horizon angles · `[x]` T11 shadow casting | ✅ **CP-2 SIGNED** 2026-07-24 |
| **Phase 3 — Physical fields** | `[x]` T12 ground surface temp · `[x]` T13 wall surface temp (two tiers) · `[x]` T14 mean radiant temperature engine · `[x]` T15 pedestrian wind field · `[x]` T16 air temperature field | ✅ **CP-3 SIGNED (full)** 2026-07-24 |
| **Phase 4 — Stage 6 orchestration** | `[x]` T17 analysis window · `[x]` T18 Stage-6 orchestrator · `[x]` T19 raster I/O & palette · `[x]` T20 exposure metrics & parcel aggregation · `[x]` T21 figures · `[x]` T22 LIVE_SMOKE on a real cell · `[x]` T23 register outdoor measurements in platform docs | ✅ **CP-4 SIGNED** 2026-07-24 |
| **Phase 5 — Extensions (v1.1)** | `[x]` T24 mitigation scenario engine · `[x]` T25 3D viewer integration · `[x]` T26 cluster fleet sweep (12 cells) | ✅ **CP-5 SIGNED** 2026-07-24 — **ARC COMPLETE** |

---

## 2. Defect ledger — E-UTCI-01 → E-UTCI-16

| ID | Short description | Status |
|---|---|---|
| E-UTCI-01 | CP-2 SVF gate failure — first adjudication | `[x]` CLOSED |
| E-UTCI-02 | CP-2 gate re-adjudication → height-adjusted target | `[x]` CLOSED |
| E-UTCI-03 | CP-3 Tmrt gate failure — first adjudication | `[x]` CLOSED |
| E-UTCI-04 | `L_sky` / `K_dir` magnitude contradiction in `mrt.py` | `[x]` CLOSED |
| E-UTCI-05 | Test regression surfaced by the E-UTCI-04 fix | `[x]` CLOSED |
| E-UTCI-06 | Second regression from the same fix | `[x]` CLOSED |
| E-UTCI-07 | T22 LIVE_SMOKE wind defect | `[x]` CLOSED |
| E-UTCI-08 | Residual wind bound violations → postcondition sanity check | `[x]` CLOSED, re-verified 0 violations domain-wide |
| **E-UTCI-09** | **Upstream `height_m` gap → zero building massing in 3–4 of 12 cells** | `[x]` **MATERIALLY FIXED, DOCUMENTED RESIDUAL — CP-C SIGNED 2026-07-25.** All three flat-field cells cleared (`svf_mean` left 1.0000, `zero_building_massing` True→False); `nyc_rural` 36.4 % / `austin_rural` 19.2 % still unknown → forwarded to a Stage-1 acquisition arc |
| **E-UTCI-10** | `spatial_impute.py` silently skips zero-neighbour rows without MNAR-flagging them | `[x]` **FIXED** by T09 — distinct `SPATIAL_NO_NEIGHBOUR_SKIPPED` token, silent-no-donor bucket → 0 |
| **E-UTCI-11** | Half-landed fusion ship — `fusion.py` + its 29 spec tests committed, but config keys and `_fusion_tier` body never landed (`test_fusion.py` = 25 failed / 4 passed on a clean tree) | `[x]` **CLOSED** — config half by T03, router body by T07; `test_fusion.py` now **29 passed** |
| **E-UTCI-12** | Second half-landed ship — `test_draw_methods.py` references `imputation._draw_tier`, which does not exist → the **whole** `pytest -q` run aborts at collection | 🔄 **OPEN** — pre-existing, out of scope, forwarded to the Stage-2 imputation owner |
| **E-UTCI-13** | T05's height cache stores *normalized* Overture output, so a re-read silently nulls `levels`/`use_class` — a future arc would misread this as "Overture has no storey data" | 🔄 **OPEN** — harmless for `height_m` (this plan's only target), documented not fixed |
| **E-UTCI-14** | `test_imputation_routing.py`'s `test_fusion_force_enabled_raises_not_implemented` asserted `_fusion_tier` always raises — obsoleted by T07 implementing it | `[x]` **FIXED** 2026-07-25 — the forward was overturned: cleaning up a test *your own change* invalidated is not scope creep, it is finishing the change. Obsolete stub-raise test retired |
| **E-UTCI-15** | Two concurrent Stage-6 runs raced on one output directory (double-dispatch on an ambiguous status message) | `[x]` **RESOLVED** (process incident) — both trees killed, both contaminated directories destroyed, single clean re-run. No shipped artifact affected |
| **E-UTCI-16** | `config.py`'s fusion comment block claimed `fusion` stays OUT of `IMPUTE_ENABLED_TIERS` — contradicting the tuple two lines above it, which T03 had put it into | `[x]` **FIXED** 2026-07-25 — same overturned forward as E-UTCI-14, caught by the user. Comment-only change; `IMPUTE_ENABLED_TIERS` untouched, 67 tests green |

---

## 3. E-UTCI-09 follow-on investigation (current work)

**Not a UTCI-arc defect** — an upstream Stage-1 (data acquisition) gap, forwarded. This investigation
**scopes and characterizes** it and proposes candidate fix shapes. **It implements no fix.**

Plan: `e-utci-09/PLAN_e-utci-09_investigation.md` · Director prompt: `prompt/DIRECTOR_PROMPT_e-utci-09-investigation_2026-07-24.md`

- `[x]` **I01** — Full 12-cell characterization (gap confirmed cleanly scoped to `height_m`/`levels`)
- `[x]` **I02** — Desk-research survey of candidate external height data sources (no live fetch) → Microsoft Global ML Building Footprints strongest candidate
- `[x]` **I03** — Structural test: does `spatial_impute.py`'s MNAR guard reject these cells? → **yes, at every radius up to 1000 m**
- `[x]` **I04** — Candidate fix shapes synthesis, ranked, none adopted → split strategy indicated
- `[x]` 🔶 **CP-INV** — investigation checkpoint, completed 2026-07-25 (**stays OPEN**, handed back to a manager session; this plan never reaches CLOSED)

📄 **Completion report:** `e-utci-09/COMPLETION_REPORT_e-utci-09-investigation.md`

**Headline finding:** narrow upstream field-level gap, not a pipeline defect — and the platform's
existing height-imputation infrastructure **cannot** fix it (`knn_fill` fills 0 rows in the 3
fully-affected cells at every radius from 100 m to 1000 m; the MNAR guard is working as designed).
**Blocking decision for the follow-up plan:** measuring Microsoft Global ML's real height coverage on
these 4 tracts requires a data download → needs CLAUDE.md §5.3 unblocked or a scoped exception.

---

## 3b. E-UTCI-09 height backfill — the follow-up FIX plan — 🔒 CLOSED 2026-07-25

Plan: `implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md` · 13 tasks, 3 checkpoints.
**CP-C signed 2026-07-25** (T01–T07, T09–T13 built; T08 closed unbuilt at CP-B). All three
flat-field cells cleared; a material rural residual is documented and forwarded out of this arc.
**Reshaped by a late discovery:** `openubem/semantic/fusion.py` already contains a complete,
spec-tested external-data fusion tier — what was missing is *configuration*, not capability. So the
fix is platform-wide (Stage 2), not Stage-6-only, and much cheaper than the investigation predicted.

| Task | | Status |
|---|---|---|
| T01 | Offline audit — prove the fusion height path is inert today | `[x]` **ACCEPTED** — `precedence_for("height_m")` → `[]`, 6 config keys absent |
| T02 | Offline proof `fuse()` fills from the committed Overture slice | `[x]` **ACCEPTED** — `value=30.0`, `token="FUSED_OVERTURE_HIGH"`, zero network |
| T03 | Config surface for the fusion sources (default-OFF) | `[x]` **ACCEPTED** — 7 keys added inert; `test_fusion.py` 25 failed → **25 passed** |
| **CP-A** | Mechanism proven offline, nothing enabled | ✅ **FULLY SIGNED** 2026-07-25 — all 4 T03 criteria manager-re-derived |
| T04 | Bounding boxes + cache layout for the 4 tracts | `[x]` **ACCEPTED** — `height_cache.py` + `manifest.json` |
| T05 | 🌐 **Scoped one-off Overture pull** — the plan's *single* network exception | `[x]` **ACCEPTED** — 4/4 pulls succeeded first attempt, one endpoint, no retry |
| T06 | Coverage census on the 4 tracts — **DECISION GATE** | `[x]` **ACCEPTED** — 80.2 / 45.0 / 92.0 / 62.0 % of the gap filled |
| **CP-B** | Coverage measured; manager picks the primary path | ✅ **SIGNED** 2026-07-25 — **CONTINUE**; coverage thin in *no* cell |
| T07 | Route `height_m` through the fusion tier (+ implement `_fusion_tier`) | `[x]` **DONE** — `test_fusion.py` 29 passed; 2.1 m min-height floor added (3 rows rejected in `nyc_suburban`); byte-identical no-op re-verified on real `la_urban` before flipping `IMPUTE_ENABLED_TIERS` |
| T08 | ~~Low-confidence regional fallback~~ | ❌ **DROPPED at CP-B** — existing spatial tier now un-blocked, in-cell donors beat `la_rural` |
| T09 | Fix E-UTCI-10 — **condition met, now required** | `[x]` **DONE** — distinct `SPATIAL_NO_NEIGHBOUR_SKIPPED` token; silent bucket 6→0 (`nyc_rural`), 13→0 (`austin_rural`) |
| T10 | Regression + provenance test suite | `[x]` **DONE** — `tests/test_height_backfill.py`, 20 new tests, 44/44 passing with `test_fusion.py` |
| T11 | Re-run Stage 6 on the 4 cells — `svf_mean` must leave 1.0000 | `[x]` **DONE** — all 4 cells leave 1.0000: `nyc_suburban` 1.0000→**0.9619**, `nyc_rural` 1.0000→**0.9972**, `austin_centre` 0.9474→**0.8426**, `austin_rural` 1.0000→**0.9935**. Before/after table (12 cells) + figure at `openubem/outputs/comparisons/t11_e_utci_09_before_after_comparison.csv` / `t11_e_utci_09_svf_before_after.png` |
| T12 | Fleet non-regression: the 8 unaffected cells must not move | `[x]` **DONE** — byte-identical fusion-on vs. fusion-off on all 8 cells; 0 observed values changed |
| T13 | Docs, registry, E-UTCI-09 disposition | `[x]` **DONE** — this checklist + `docs/PROJECT_CHECKLIST.md` + `OpenUBEM_outdoor_analysis_reference.md` §3.3.1 (new) + `OpenUBEM_imputation_methods.md` §4.1 all updated; parent-plan §10 disposition text prepared for the manager, not written by this dispatch |
| **CP-C** | Final audit | 🔶 **ready for manager audit** — T01–T13 all done; manager writes the parent plan's §9/§10 disposition |

**Manager decisions already taken** (delegated by the user 2026-07-25): a narrowly-scoped one-off
network exception for **T05 only** (CLAUDE.md §5.3 stays blocked — this is a one-time cached data
acquisition, *not* a live-network integration test, and is not precedent); and **Overture as the
primary source** (it ingests Microsoft ML building footprints through already-tested code), LiDAR
wired but unfed, regional LOW-confidence fallback only if T06's census justifies it.

**Where this can still stop:** CP-A if T03 regresses anything real · T05 if the pull fails (no
substitute source will be improvised) · CP-B if Overture coverage is thin in all four cells — in
which case the plan closes with the census attached and no fix, which is a legitimate outcome.

---

**The gap, in one line (as found, pre-fix):** 3 of 12 validated cells (`nyc_suburban` 1589/1589,
`nyc_rural` 198/198, `austin_rural` 245/245) have `height_m` NaN for 100 % of buildings, and
`austin_centre` for 84.5 % (349/413) — so Stage 6 excludes them from the DSM and the domain
computes as a flat open field (`svf_mean = 1.0000`) instead of an urban canyon.

**Post-fix, in one line:** T07/T11 route `height_m` through the fusion tier + spatial donors; all 4
cells now leave `svf_mean = 1.0000`, but a documented residual remains `NaN` and excluded from the
massing — 15/1589 `nyc_suburban` (0.9 %), 72/198 `nyc_rural` (36.4 %), 11/349 `austin_centre`
(3.2 % of its gap), 47/245 `austin_rural` (19.2 %). **Materially fixed, not fully closed.**

---

## 4. Where things live

| You want… | Go to |
|---|---|
| The full technical record (frozen) | `implementation/PLAN_utci_microclimate_implementation.md` |
| The plain-language description of what UTCI is | `UTCI Technical Description.md` |
| The completed E-UTCI-09 investigation | `e-utci-09/` |
| The closed height-backfill fix plan | `implementation/sub-plans/DONE-PLAN_e-utci-09_height_backfill.md` |
| The Stage-6 results write-up | `results/OpenUBEM_results_UTCI_microclimate.md` |
| Result figures and evidence bundles | `results/` and `openubem/outputs/` (flat) |
| Background literature review | `DeepResearches/` |
| The summary-graphic prompt | `abstract-image/` |
| Every outdoor/site metric this arc registered | `docs/docs_EXPLANATION/OpenUBEM_outdoor_analysis_reference.md` |

---

*Tracking surface only — the binding record is each plan's own §7/§9 progress log and §8/§10 error log.*
